"""
benchmark形式评估集推理
"""
import os
import sys
os.environ["CUDA_VISIBLE_DEVICES"] = "7"
import time
import torch
import copy
import jsonlines
from tqdm import tqdm
from transformers import (
    AutoModelForCausalLM, AutoTokenizer
)
import torch, transformers, pdb, json


class ChatQwen:
    def __init__(self,
            model_name_or_path: str = "kwaikeg/kagentlms_qwen_7b_mat",
        ) -> None:

        print('loading tokenizer')
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            use_fast=False,
            padding_side='left',
            trust_remote_code=True
        )
        self.tokenizer.add_special_tokens({'additional_special_tokens': ['<|im_end|>']}, replace_additional_special_tokens=False)

        print(f'loading model: {model_name_or_path}')
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code = True
        ).eval()
        print('loaded')



    def encode(self, tokenizer, query, history, system='You are a helpful assistant.'):
        prompt_ids = []
        history = history + [(query, None)]
        kwargs = dict(allowed_special="all", add_special_tokens=False)
        sep = ['<|im_end|>','\n']
        sep_ids = []
        for s in sep:
            sep_ids += tokenizer.encode(s, **kwargs)
        for turn_idx, (q, r) in enumerate(history):
            if turn_idx == 0:
                prefix = ['<|im_start|>',f'system\n{system}']
                prefix_ids = []
                for p in prefix:
                    prefix_ids += tokenizer.encode(p, **kwargs)
                prefix_ids += sep_ids
            else:
                prefix_ids = sep_ids
            prompt = ['<|im_start|>',f'user\n{q}','<|im_end|>','\n','<|im_start|>','assistant\n']
            query_ids = []
            for p in prompt:
                query_ids = query_ids + tokenizer.encode(p, **kwargs)
            resp_ids = tokenizer.encode(r, **kwargs) if r is not None else []
            prompt_ids = prompt_ids + prefix_ids + query_ids + resp_ids
        return prompt_ids 

    def chat(self, query, history=list(), system="",
                    prune_text=None,
                    num_beams=1,
                    temperature=0.1,
                    top_p=0.75,
                    top_k=40,
                    repetition_penalty=1.0,
                    max_new_tokens=520,
                    input_max_length=3096,
                    *args, **kwargs
                ):

        prompt_tokens = self.encode(tokenizer=self.tokenizer, query=query, history=history, system=system)

        if len(prompt_tokens) > input_max_length:
            if prune_text is None or prune_text not in query:
                prompt_tokens = prompt_tokens[:input_max_length//2] + prompt_tokens[-input_max_length//2:]
            else:
                print('memory截断')
                prune_text_prompt_tokens = self.tokenizer.encode(prune_text,add_special_tokens=False)
                sublst_len = len(prune_text_prompt_tokens)
                start_index = None
                for i in range(len(prompt_tokens) - sublst_len + 1):
                    if prompt_tokens[i:i+sublst_len] == prune_text_prompt_tokens:
                        start_index = i
                        break
                
                if start_index is None:
                    prompt_tokens = prompt_tokens[:input_max_length//2] + prompt_tokens[-input_max_length//2:]
                else:
                    # 除了memory的其他部分的长度
                    other_len = len(prompt_tokens) -  sublst_len
                    if input_max_length > other_len:
                        max_memory_len = input_max_length - other_len
                        prune_text_prompt_tokens = prune_text_prompt_tokens[:max_memory_len//2]+prune_text_prompt_tokens[-max_memory_len//2:]
                        prompt_tokens = prompt_tokens[:start_index] + prune_text_prompt_tokens + prompt_tokens[start_index+sublst_len:]


        prompt = self.tokenizer.decode(prompt_tokens, skip_special_tokens=True)
    
        input_ids = torch.tensor([prompt_tokens], device=self.model.device)
        prompt_length = len(input_ids[0])
        gen_kwargs = dict(
            input_ids = input_ids,
            num_beams = num_beams,
            temperature = temperature,
            top_p = top_p,
            top_k = top_k,
            repetition_penalty = repetition_penalty
        )
        generation_output = self.model.generate(**gen_kwargs)
        outputs = generation_output.tolist()[0][prompt_length:]
        response = self.tokenizer.decode(outputs, skip_special_tokens=True)

        new_history = history[:] + [[query, response]]

        return response, new_history

def infer_to_file(eval_file, infer_out_file, gpt_bot):
    print(f"load eval data from {eval_file}")
    eval_data_list  = []
    with jsonlines.open(eval_file,"r") as f:
        eval_data_list = [obj for obj in f]
    
    with jsonlines.open(infer_out_file,'w') as w:
        for obj in tqdm(eval_data_list):
            new_obj = copy.deepcopy(obj)
            type = obj["type"]
        
            memory = obj["memory"]
            if type == "profile":
                query = obj["prompt_input"]["prompt"]
                response, history= gpt_bot.chat(query=query, prune_text=memory)
                new_obj["model_predict"] = response
            else:
                infer_dict = {}
                for prompt_key,prompt_in in obj["prompt_input"].items():
                    query = prompt_in
                    response, history = gpt_bot.chat(query=query, prune_text=memory)
                    infer_dict[prompt_key] = response
                new_obj["model_predict"] = infer_dict

            w.write(new_obj)

    print(f"infer out save to  {infer_out_file}")



def run(save_file):
    gpt_bot = ChatQwen()

    eval_file = "./benchmark_eval.jsonl"
    infer_to_file(eval_file,save_file,gpt_bot)

if __name__=='__main__':

    run(sys.argv[1])