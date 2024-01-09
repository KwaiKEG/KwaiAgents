"""
进行benchmark的评估，包括：plan、tooluse、reflextion、conclusion、profile和最终score
"""
import json, re, math, sys, logging, nltk, os, unicodedata, pandas as pd, time
import contextlib
import jsonlines
from tqdm import tqdm
from typing import Optional
from rouge import Rouge 
from rouge_chinese import Rouge as RougeCh 
from nltk.translate.bleu_score import sentence_bleu
from collections import defaultdict
print(sys.getrecursionlimit())

# Rouge的LCS使用，增大递归次数
sys.setrecursionlimit(4096 * 4096)

nltk.download('punkt')

def mixed_tokenize(sentence):
    tokens = nltk.word_tokenize(sentence)
    result = []
    for token in tokens:
        if any('Lo' == unicodedata.category(ch) for ch in token):
            # 'Lo' is the unicode category of all non-punctuation/symbol CJK characters # result.extend(jieba.cut(token, cut_all=False))
            result.extend(list(token))
        else:
            result.append(token)
    return result


def rouge_score(label,predict):
    """
    计算rouge-L 
    """
    label,predict = str(label), str(predict)
    if label == '' or predict == '':
        return 0
    rouge = RougeCh()
    predict = " ".join(mixed_tokenize(predict))
    label = " ".join(mixed_tokenize(label))
    scores = rouge.get_scores(predict, label)
    return scores[0]["rouge-l"]["f"]


def autogpt_response_process(gpt_out):
    if "web_search(" in gpt_out:
        gpt_out = ""
    if "response=\"" in gpt_out:
        gpt_out = gpt_out.split("response=\"")[1].replace("\")","")
    return gpt_out

def toolllama_response_process(gpt_out):
    if """\"final_answer\": \"""" in gpt_out:
        gpt_out = gpt_out.split("""\"final_answer\": \"""")[1].replace("\"","").replace("}","")
    if gpt_out == "\n":
        gpt_out = ""
    return gpt_out

def find_json_dict(input_str, cnt=0):
    if input_str.count("{") > input_str.count("}"):
        return find_json_dict(input_str.rstrip("\n") + "\n}", cnt + 1)
    if cnt >= 5:
        return input_str
    try:
        st = input_str.index("{")
        end_str = '}\n}'
        end = input_str.rindex(end_str)
        return input_str[st:end + len(end_str)].strip()
    except json.decoder.JSONDecodeError:
        return find_json_dict(input_str.rstrip("\n") + "\n}", cnt + 1)
    except:
        return input_str

def add_quotes_to_property_names(json_string: str) -> str:
    """
    Add quotes to property names in a JSON string.

    Args:
        json_string (str): The JSON string.

    Returns:
        str: The JSON string with quotes added to property names.
    """

    def replace_func(match: re.Match) -> str:
        return f'"{match[1]}":'

    property_name_pattern = re.compile(r"(\w+):")
    corrected_json_string = property_name_pattern.sub(replace_func, json_string)

    try:
        json.loads(corrected_json_string)
        return corrected_json_string
    except json.JSONDecodeError as e:
        raise e


def balance_braces(json_string: str) -> Optional[str]:
    """
    Balance the braces in a JSON string.

    Args:
        json_string (str): The JSON string.

    Returns:
        str: The JSON string with braces balanced.
    """

    open_braces_count = json_string.count("{")
    close_braces_count = json_string.count("}")

    while open_braces_count > close_braces_count:
        json_string += "}"
        close_braces_count += 1

    while close_braces_count > open_braces_count:
        json_string = json_string.rstrip("}")
        close_braces_count -= 1

    with contextlib.suppress(json.JSONDecodeError):
        json.loads(json_string)
        return json_string


def correct_json(json_to_load: str) -> str:
    """
    Correct common JSON errors.
    Args:
        json_to_load (str): The JSON string.
    """

    try:
        json.loads(json_to_load)
        return json_to_load
    except json.JSONDecodeError as e:
        error_message = str(e)
        if error_message.startswith("Invalid \\escape"):
            json_to_load = fix_invalid_escape(json_to_load, error_message)
        if error_message.startswith(
            "Expecting property name enclosed in double quotes"
        ):
            json_to_load = add_quotes_to_property_names(json_to_load)
            try:
                json.loads(json_to_load)
                return json_to_load
            except json.JSONDecodeError as e:
                error_message = str(e)
        balanced_str = balance_braces(json_to_load)
        if balanced_str:
            return balanced_str
    return json_to_load

def fix_invalid_escape(json_to_load: str, error_message: str) -> str:
    """Fix invalid escape sequences in JSON strings.

    Args:
        json_to_load (str): The JSON string.
        error_message (str): The error message from the JSONDecodeError
          exception.

    Returns:
        str: The JSON string with invalid escape sequences fixed.
    """
    while error_message.startswith("Invalid \\escape"):
        bad_escape_location = extract_char_position(error_message)
        json_to_load = (
            json_to_load[:bad_escape_location] + json_to_load[bad_escape_location + 1 :]
        )
        try:
            json.loads(json_to_load)
            return json_to_load
        except json.JSONDecodeError as e:
            # print("json loads error - fix invalid escape", e)
            error_message = str(e)
    return json_to_load

def extract_char_position(error_message: str) -> int:
    """Extract the character position from the JSONDecodeError message.

    Args:
        error_message (str): The error message from the JSONDecodeError
          exception.

    Returns:
        int: The character position.
    """

    char_pattern = re.compile(r"\(char (\d+)\)")
    match = char_pattern.search(error_message)
    if match:
        return int(match[1])
    else:
        raise ValueError("Character position not found in the error message.")


def get_ReACT_plan_and_tool(response, funcs):
    thought, tool_name, tool_args_kv = 'None','None',{}

    thought = re.findall(r"(.+?)(?=(Final Answer|\Z|Action))", response, re.DOTALL)[0][0].strip()
    
    def get_react_func_key(func_name, funcs):
        key = 'None'
        for func in funcs:
            if func['name'] == func_name:
                try:
                    key = list(func['parameters']['properties'].keys())[0]
                except:
                    key = 'None'
        return key

    tool_name_re = re.findall(r"Action:(.+?)Action Input:", response, re.DOTALL)
    if len(tool_name_re) > 0:
        tool_name = tool_name_re[0].strip()
        key = get_react_func_key(tool_name, funcs)
        if key != 'None':
            value = re.findall(r"Action Input:(.+?)(?=(Observation|\Z))", response, re.DOTALL)
            if len(value) > 0:
                tool_args_kv = {
                    key: value[0][0].strip()
            }
    
    # 没有keys，统一为 None
    if thought == '':
        thought == 'None'
    if tool_name == '':
        tool_name = 'None'
    if tool_args_kv == '':
        tool_args_kv = {}
    
    return thought, tool_name, tool_args_kv


def get_AutoGPT_plan_and_tool(response):
    thought, tool_name, tool_args_kv = 'None','None',{}
    try:
        response = correct_json(find_json_dict(response))
        res_json = json.loads(response)
        assert isinstance(res_json,dict)
    except:
        return thought, tool_name, tool_args_kv
    
    if 'thoughts' in res_json:
        if res_json['thoughts'] and 'text' in res_json['thoughts']:
            thought = res_json['thoughts']['text']

    if 'command' in res_json:
        if res_json['command'] and 'name' in res_json['command']:
            tool_name = res_json['command']['name']
        if res_json['command'] and 'args' in res_json['command']:
            try:
                assert isinstance(res_json['command']['args'],dict)
                tool_args_kv = res_json['command']['args']
            except:
                pass
                
    if thought == '':
        thought == 'None'
    if tool_name == '':
        tool_name = 'None'
    if tool_args_kv == '':
        tool_args_kv = {}

    return thought, tool_name, tool_args_kv


def get_ToolLlama_plan_and_tool(response):
    thought,tool_name,tool_args_kv = 'None','None',{}

    try:
        thought = re.findall(r"Thought:(.+?)(?=(\Z|Action))", response, re.DOTALL)
        if len(thought) > 0:
            thought = thought[0][0].strip()
        tool_name_re = re.findall(r"Action:(.+?)(?=(Action Input:|\Z))", response, re.DOTALL)
        if len(tool_name_re) > 0:
            tool_name = tool_name_re[0][0].strip()
            tool = re.findall(r"Action Input:(.+?)(?=(Thought|\Z))", response, re.DOTALL)
            if len(tool) > 0:
                tool = tool[0][0].strip()
                try:
                    tool = correct_json(find_json_dict(tool))
                    tool_json = json.loads(tool)
                    assert isinstance(tool_json,dict) 
                    tool_args_kv = tool_json
                except:
                    # print('tool is not a dict')
                    pass
    except:
        pass

    if thought == '':
        thought == 'None'
    if tool_name == '':
        tool_name = 'None'
    if tool_args_kv == '':
        tool_args_kv = {}

    return thought, tool_name, tool_args_kv

def get_KuaiAgent_plan_and_tool(response):
    thought,tool_name,tool_args_kv = 'None','None',{}

    try:
        response = correct_json(find_json_dict(response))
        res_json = json.loads(response)
        assert isinstance(res_json,dict)
    except:
        # print('KuaiAgent JSON 格式错误')
        return thought,tool_name,tool_args_kv
    
    if 'task_name' in res_json:
        thought = res_json['task_name']

    if res_json and 'command' in res_json:
        if 'name' in res_json['command']:
            tool_name = res_json['command']['name']
        if 'args' in res_json['command']:
            try:
                assert isinstance(res_json['command']['args'],dict) 
                tool_args_kv = res_json['command']['args']
            except:
                # print('arg is not a dict')
                pass

    if thought == '':
        thought == 'None'
    if tool_name == '':
        tool_name = 'None'
    if tool_args_kv == '':
        tool_args_kv = {}

    return thought, tool_name, tool_args_kv

def get_ModelScope_plan_and_tool(response):
    thought,tool_name,tool_args_kv = 'None','None',{}

    task = re.findall(r"\<\|startofthink\|\>(.+?)\<\|endofthink\|\>", response, re.DOTALL)
    if len(task) > 0:
        task = task[0].strip()
        try:
            task = correct_json(find_json_dict(task))
            task = json.loads(task)
            assert isinstance(task,dict)
        except:
            # print('KuaiAgent JSON 格式错误')
            return thought,tool_name,tool_args_kv

        if task and 'api_name' in task:
            tool_name = task['api_name']
        if task and 'parameters' in task:
            try:
                assert isinstance(task['parameters'],dict) 
                tool_args_kv = task['parameters']
            except:
                # print('arg is not a dict')
                pass
    
    if thought == '':
        thought == 'None'
    if tool_name == '':
        tool_name = 'None'
    if tool_args_kv == '':
        tool_args_kv = {}
    
    return thought, tool_name, tool_args_kv



def get_plan_metric(golden_thoughts, golden_toolnames, thought, tool_name):
    plan_metrics = []
    for golden_thought, golden_toolname in zip(golden_thoughts,golden_toolnames):
        if golden_thought == 'None' or golden_toolname == 'None':
            continue
        thought_rouge = rouge_score(golden_thought, thought)
        tool_em = 1 if tool_name == golden_toolname else 0
        plan_metrics.append(thought_rouge * tool_em)
    if len(plan_metrics) == 0:
        plan_metrics = [0.]
    return max(plan_metrics)




def get_tool_metric(golden_toolnames, golden_tool_args, tool_name, tool_args):
    tool_metrics = []
    for golden_toolname, golden_tool_arg in zip(golden_toolnames, golden_tool_args):
        if golden_toolname == 'None':
            continue
        tool_em = 1 if tool_name == golden_toolname else 0
        avg_arg_rouges = []
        if golden_tool_arg == {} and tool_args == {}:
            avg_arg_rouges = [1.]
        elif tool_args != {}:
            for k,v in golden_tool_arg.items():
                match_k = False
                for k1,v1 in tool_args.items():
                    if k1 == k:
                        avg_arg_rouges.append(rouge_score(v, v1))
                        match_k = True
                        break
                if not match_k:
                    avg_arg_rouges.append(0.)
        else:
            avg_arg_rouges = [0.]
        arg_rouge = sum(avg_arg_rouges) / len(avg_arg_rouges) if len(avg_arg_rouges)>0 else 0 
        tool_metrics.append(arg_rouge * tool_em)

    if len(tool_metrics) == 0:
        tool_metrics = [0.]
    return max(tool_metrics)


def get_reflextion_metric(golden_thoughts, golden_toolnames, golden_tool_args, last_task_info, thought, tool_name, tool_args):
    reflextion_metrics = []
    for golden_thought, golden_toolname, golden_tool_arg in zip(golden_thoughts,golden_toolnames, golden_tool_args):
        if golden_thought == 'None' or golden_toolname == 'None':
            continue
        thought_rouge = rouge_score(golden_thought, thought)
        tool_em = 1 if tool_name == golden_toolname else 0
        avg_arg_rouges = []
        if golden_tool_arg == {} and tool_args == {}:
            avg_arg_rouges = [1.]
        elif tool_args != {}:
            for k,v in golden_tool_arg.items():
                match_k = False
                for k1,v1 in tool_args.items():
                    if k1 == k:
                        avg_arg_rouges.append(rouge_score(v, v1))
                        match_k = True
                        break
                if not match_k:
                    avg_arg_rouges.append(0.)
        else:
            avg_arg_rouges = [0.]
        arg_rouge = sum(avg_arg_rouges) / len(avg_arg_rouges) if len(avg_arg_rouges)>0 else 0 
        # 惩罚因子，如果和上一轮相同则penalty_weight为1，进行惩罚
        if last_task_info["tool_name"] == golden_toolname and last_task_info["tool_args"]== golden_tool_arg:
            penalty_weight = 1
        else:
            penalty_weight = 0
        reflextion_score = (1-penalty_weight) * (0.3 * tool_em * thought_rouge + 0.7 * tool_em * arg_rouge)
        reflextion_metrics.append(reflextion_score)

    return max(reflextion_metrics)

def plan_tooluse_reflextion_predict(model_predict, funcs):
    
    predict_parsed_list = []
    for prompt, predict in model_predict.items():
        if prompt == 'ReACT' and predict != "":
            thought, tool_name, tool_args_kv = get_ReACT_plan_and_tool(predict, funcs)
        elif prompt == 'AutoGPT':
            thought, tool_name, tool_args_kv = get_AutoGPT_plan_and_tool(predict)
        elif prompt == 'ToolLlama':
            thought, tool_name, tool_args_kv = get_ToolLlama_plan_and_tool(predict)
        elif prompt == 'ModelScope':
            thought, tool_name, tool_args_kv = get_ModelScope_plan_and_tool(predict)
        elif prompt == 'KuaiAgent':
            thought, tool_name, tool_args_kv = get_KuaiAgent_plan_and_tool(predict)
        result = {
            'thought': thought,
            'tool_name': tool_name,
            'tool_args': tool_args_kv,
        }
        predict_parsed_list.append(result)

    return predict_parsed_list

def conclusion_metrics(label_dict, predict_dict):
    """
    计算conclusion的分数
    """
    all_rouge = []
    for id, obj in tqdm(predict_dict.items()):
        label_response_dict_list = label_dict[id]["golden_result_list"]
        label_response_list = []
        for i in label_response_dict_list:
            label_response_list.append(i["golden_result"])
        predict_parsed_list = obj["model_predict"]

        rouge_list = []
        predict_pre_template_score = []

        for key,predict in predict_parsed_list.items():
            # 格式单独处理
            if key == "AutoGPT":
                predict = autogpt_response_process(predict)
            if key == "ToolLlama":
                predict = toolllama_response_process(predict)

            predict_pre_label_score = []
            if predict == "":
                predict_pre_label_score.append(0)
            else:
                if type(predict) == dict:
                    predict = json.dumps(predict,ensure_ascii=False)
                for label in label_response_list:
                    rouge_res = rouge_score(label,predict)
                    predict_pre_label_score.append(rouge_res)
            predict_pre_template_score.append(max(predict_pre_label_score))

        all_rouge.append(sum(predict_pre_template_score)/len(predict_pre_template_score))

    conclusion_avg_rouge = sum(all_rouge)/len(all_rouge)

    return conclusion_avg_rouge

def profile_metrics(label_dict, predict_dict):
    """
    计算profile 的平均Rouge
    """
    all_rouge = []
    for id, obj in tqdm(predict_dict.items()):
        label_response_dict_list = label_dict[id]["golden_result_list"]
        label_response_list = []
        for i in label_response_dict_list:
            label_response_list.append(i["golden_result"])
        predict = obj["model_predict"]

        rouge_list = []
        if predict == "":
            all_rouge.append(0)
        else:
            for label in label_response_list:
                rouge_res = rouge_score(label,predict)
                rouge_list.append(rouge_res)
            all_rouge.append(max(rouge_list))
    profile_avg_rouge = sum(all_rouge)/len(all_rouge)
    return profile_avg_rouge



def plantooluse_metrics(label_dict, predict_dict):
    all_plan_rouge = []
    all_tooluse_rouge = []
    for id, obj in tqdm(predict_dict.items()):
        label_response_list = [i for i in label_dict[id]["golden_result_list"]]
        funcs = label_dict[id]["funcs"]
        predict_parsed_list = plan_tooluse_reflextion_predict(obj["model_predict"], funcs)
        plan_rouge_list = []
        tooluse_rouge_list = []
        label_thoughts = []
        label_tool_names = []
        label_tool_args = []
        query = obj["query"]
        for label in label_response_list:
            label_thoughts.append(label["thought"])
            label_tool_names.append(label["tool_name"])
            label_tool_args.append(label['tool_args'])
        for predict in predict_parsed_list:
            plan_metric = get_plan_metric(label_thoughts, label_tool_names, predict['thought'], predict['tool_name'])
            tool_metric = get_tool_metric(label_tool_names, label_tool_args, predict['tool_name'], predict['tool_args'])
            plan_rouge_list.append(plan_metric)
            tooluse_rouge_list.append(tool_metric)

        # plan_metric内部做过max，外部求mean
        all_plan_rouge.append(sum(plan_rouge_list)/len(plan_rouge_list))
        all_tooluse_rouge.append(sum(tooluse_rouge_list)/len(tooluse_rouge_list))

    plan_avg_score = sum(all_plan_rouge) / len(all_plan_rouge)
    tooluse_avg_score = sum(all_tooluse_rouge) / len(all_tooluse_rouge)
    return plan_avg_score, tooluse_avg_score




def reflextion_metrics(label_dict, predict_dict):
    all_reflextion_score = []
    query_score = {}
    for id, obj in predict_dict.items():
        label_response_list = [i for i in label_dict[id]["golden_result_list"]]
        predict_parsed_list = []
        query = obj["query"]
        funcs = label_dict[id]["funcs"]
        predict_parsed_list = plan_tooluse_reflextion_predict(obj["model_predict"], funcs)
        last_task_info = label_dict[id]["memory_last_task"]
        reflextion_score_list = []
        label_thoughts = []
        label_tool_names = []
        label_tool_args = []
        for label in label_response_list:
            label_thoughts.append(label["thought"])
            label_tool_names.append(label["tool_name"])
            label_tool_args.append(label['tool_args'])

        for predict in predict_parsed_list:
            reflextion_metric = get_reflextion_metric(label_thoughts, label_tool_names, label_tool_args, last_task_info, predict['thought'], predict['tool_name'], predict['tool_args'])
            reflextion_score_list.append(reflextion_metric)
        all_reflextion_score.append(sum(reflextion_score_list)/len(reflextion_score_list))


    reflextion_avg_score = sum(all_reflextion_score)/len(all_reflextion_score)
    return reflextion_avg_score




def eval(eval_file, predict_file):
    """
    进行整体评估
    """
    print(f"load eval file from {eval_file}")
    print(f"load predict file from {predict_file}")
    plan_tooluser_label = {}
    reflextion_label = {}
    conclusion_label = {}
    profile_label = {}

    with jsonlines.open(eval_file,"r") as f:
        for line in f:
            type = line["type"]
            id  = line["id"]
            if type == "plantooluse":

                plan_tooluser_label[id] = line
            if type == "reflextion":
                reflextion_label[id] = line
            if type == "conclusion":
                conclusion_label[id] = line 
            if type == "profile":
                profile_label[id] = line


    plan_tooluser_predict = {}
    reflextion_predict = {}
    conclusion_predict = {}
    profile_predict = {}

    with jsonlines.open(predict_file,"r") as f:
        for line in f:
            type = line["type"]
            id  = line["id"]
            if type == "plantooluse":
                plan_tooluser_predict[id] = line
            if type == "reflextion":
                reflextion_predict[id] = line
            if type == "conclusion":
                conclusion_predict[id] = line 
            if type == "profile":

                profile_predict[id] = line
    assert len(plan_tooluser_label) == len(plan_tooluser_predict)
    assert len(reflextion_label) == len(reflextion_predict)
    assert len(conclusion_label) == len(conclusion_predict)
    assert len(profile_label) == len(profile_predict)

    plan_score, tooluse_score = plantooluse_metrics(plan_tooluser_label, plan_tooluser_predict)
    reflextion_score = reflextion_metrics(reflextion_label, reflextion_predict)
    conclusion_score = conclusion_metrics(conclusion_label, conclusion_predict)
    profile_score = profile_metrics(profile_label, profile_predict)
    overall_score = (
        0.25 * plan_score +  # Weight for 'plantooluse' score
        0.35 * tooluse_score     +  # Weight for 'tooluse' score
        0.1 * reflextion_score  +  # Weight for 'reflection' score
        0.2 * conclusion_score  +  # Weight for 'conclusion' score
        0.1 * profile_score       # Weight for 'profile' score
    )
    print(f"plan : {plan_score*100:.2f}, tooluse : {tooluse_score*100:.2f}, reflextion : {reflextion_score*100:.2f}, conclusion : {conclusion_score*100:.2f}, profile : {profile_score*100:.2f}, overall : {overall_score*100:.2f}")






if __name__ == "__main__":
    eval(sys.argv[1], sys.argv[2])
    



    

