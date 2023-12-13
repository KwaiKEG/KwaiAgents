"""
benchmark形式评估集推理
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "7"
import sys
import time
import copy
import jsonlines
from tqdm import tqdm
from vllm import LLM, SamplingParams
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers, datetime, json

class ChatBaichuan:
    def __init__(self,
            model_name_or_path: str = "kwaikeg/kagentlms_baichuan2_13b_mat",
            template: str = 'baichuan2',
            input_max_length = 4096,
        ) -> None:

        assert template in ['baichuan', 'baichuan2']
        self.template = template

        print('loading tokenizer')
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            use_fast=False,
            padding_side='right',
            trust_remote_code=True
        )

        print('loading model')
        self.model = LLM(
            model = model_name_or_path,
            trust_remote_code=True, 
            max_num_batched_tokens=input_max_length
        )
        print('loaded')




    def encode(self, tokenizer, query, history, system=''):
        prompt_ids = []
        history = history + [(query, None)]
        kwargs = dict(add_special_tokens=False)
        for turn_idx, (q, r) in enumerate(history):
            prefix_ids = tokenizer.encode(system, **kwargs) if turn_idx == 0 else []
            if self.template == 'baichuan':
                prompt = ['<reserved_102>',q,'<reserved_103>']
            elif self.template == 'baichuan2':
                prompt = ['<reserved_106>',q,'<reserved_107>']
            query_ids = []
            for p in prompt:
                query_ids = query_ids + tokenizer.encode(p, **kwargs)
            resp_ids = tokenizer.encode(r, **kwargs) if r is not None else []
            prompt_ids = prompt_ids + prefix_ids + query_ids + resp_ids
        return prompt_ids 

    def chat(self, query, *args, **kwargs):
        mode = 'SINGLE_INFER' # 单条推理

        try:
            if type(json.loads(query)) == list:
                mode = 'BATCH_INFER'
        except:
            pass
    
        if mode == 'SINGLE_INFER':
            return self.chat_single(query, *args, **kwargs)
        elif mode == 'BATCH_INFER':
            return self.chat_batch(json.loads(query), *args, **kwargs)
        else:
            raise TypeError(f'query必须为str或list,当前为{type(query)}')

    def chat_single(self, query, history=list(), system="", chat_id=None, 
                    prune_text=None,
                    temperature=0.1,
                    top_p=0.75,
                    top_k=40,
                    repetition_penalty=1.0,
                    max_new_tokens=520,
                    input_max_length=3400,
                    *args, **kwargs
                ):

        prompt_tokens = self.encode(tokenizer=self.tokenizer, query=query, history=history, system=system)
        print('token len:',len(prompt_tokens))

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
    
        gen_kwargs = dict(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_new_tokens,
        )
        
        generation_output = self.model.generate(prompt, SamplingParams(**gen_kwargs))

        try:
            res = generation_output[0].outputs[0]
            response = res.text
        except:
            response = 'error'

        history = history[:] + [[query, response]]

        return response, history


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
    gpt_bot = ChatBaichuan()
    eval_file = "./benchmark_eval.jsonl"
    infer_to_file(eval_file,save_file,gpt_bot)

if __name__=='__main__':

    run(sys.argv[1])
