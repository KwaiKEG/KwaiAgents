import json

from kwaiagents.utils.date_utils import get_current_time_and_date
from kwaiagents.utils.function_utils import transform_to_openai_function


planning_prompt_template = """
你是{agent_name}，{agent_bio}
{agent_instructions}
当前阶段是任务规划阶段，你将给定目标或问题，你的决策将独立执行而不依赖于人类的帮助，请发挥LLM的优势并且追求高效的策略进行任务规划。
1.你有~4000字的短期记忆
2.不需要用户的帮助
3.规划的时候可以用参考工具中提到的工具
4.互联网搜索、信息聚合和鉴别真伪的能力
5.保持谦逊，对自己没把握的问题，尽可能调用command，但尽量少调用，不能重复调用
6.当你从自身知识或者历史记忆中能得出结论，请聪明且高效，完成任务并得出结论
7.经常建设性地自我批评整个行为大局，反思过去的决策和策略，以改进你的方法
8.你最多只能进行{max_iter_num}步思考，规划{max_iter_num}个任务，所以尽可能高效规划任务
9.你有反思能力，如果已完成的任务和结果暂不能得到回答问题所需信息或尚不能完成目标，应继续规划，但不能跟之前任务重复

{tool_specification}

{current_date_and_time}

{memory}

GOAL:{goal}

\n根据目标和已有任务，规划一个新Task(不能重复)，你只能以以下json列表的格式生成Task
{{
    "task_name": "任务描述",
    "command":{{
        "name":"command name",
        "args":{{
            "arg name":"value"
        }}
    }}
}}
确保Task可以被Python的json.loads解析

当已完成的Tasks已经能够帮助回答这个目标，则尽可能生成任务完成Task，否则生成一个其他Task。一个新Task:
""".strip()

planning_prompt_template_en = """
You are a {agent_name}，{agent_bio}
{agent_instructions}
Currently, you are in the task planning phase, where you will be given specific goals or problems to address. \
Your decisions will be executed independently without relying on human assistance. \
Please utilize LLM's advantages and pursue efficient strategies for task planning.\

1. You have a short-term memory of approximately 4,000 characters.
2. You do not require assistance from users.
3. You can use the reference tools mentioned when planning.
4. You have the abilities to perform internet searches, aggregate information, and discern between genuine and fake information.
5. Remain humble and, if unsure about an issue, make use of commands when possible but minimize their usage and avoid repetition.
6. When drawing conclusions from your knowledge or historical memory, be clever and efficient in task completion and conclusion.
7. Regularly engage in constructive self-criticism to reflect on past decisions and strategies and improve your approach.
8. You can think and plan up to {max_iter_num} steps, so strive to plan tasks as efficiently as possible.
9. You have the capability for reflection; if a completed task and its results cannot provide the necessary information to answer a question or achieve a goal, continue planning but avoid repeating previous tasks.

{tool_specification}

{current_date_and_time}

{memory}

GOAL:{goal}

\nBased on the goal and existing tasks, plan a new Task (no repetitions), and you can only generate the Task in the following json list format:
{{
    "task_name": "task description",
    "command":{{
        "name":"command name",
        "args":{{
            "arg name":"value"
        }}
    }}
}}
Ensure that the Task can be parsed by Python's json.loads function. 

If the already completed Tasks are sufficient to answer the goal, then try to generate the Task to complete it as much as possible. Otherwise, create another Task. 
A new Task:
""".strip()


conclusion_prompt_template = """
你是{agent_name}，{agent_bio}，{agent_instructions}
当前阶段是总结阶段，在前几次交互中，对于用户给定的目标和问题，你已经通过自己搜寻出了一定信息，你需要整合这些信息用中文给出最终的结论。
1. 搜寻的信息从很多工具中获取，会出现冗余
2. 当不同工具获取的信息冲突的时候，你应该遵循一定的优先级(Wiki > search)去解决冲突

{current_date_and_time}

{memory}

问题或目标：{goal}\n生成对用户有帮助的中文回答:
"""

conclusion_prompt_template_en = """
You are a {agent_name},{agent_bio},{agent_instructions}
The current stage is the concluding stage. In the previous interactions, \
you have already found some information by searching on your own for the user's given goals and problems. \
You need to integrate this information and provide the final conclusion in Chinese.
If there is information from Knowledge info, and the information can answer the question, \
you can use the Knowledge info information as much as possible to answer the question without using external tool results or creating your own content.
1. The information you search for comes from many sources and may be redundant.
2. When the information obtained from different tools conflicts, you should follow a certain priority (Knowledge info > Wiki > search) to resolve the conflict.

{current_date_and_time}

{memory}

Goal: {goal}
Generate helpful answers **in English** for users:
"""


def make_planning_prompt(agent_profile, goal, used_tools, memory, max_tokens_num, tokenizer, lang="en"):
    tool_spec = make_tool_specification(used_tools, lang)
    template = planning_prompt_template if lang == "zh" else planning_prompt_template_en
    prompt = template.format(**{
        "agent_name": agent_profile.name,
        "agent_bio": agent_profile.bio,
        "agent_instructions": agent_profile.instructions,
        "max_iter_num": agent_profile.max_iter_num,
        "tool_specification": tool_spec,
        "current_date_and_time": get_current_time_and_date(lang),
        "memory": memory,
        "goal": goal
    })
    prompt = prompt_truncate(tokenizer, prompt, memory, max_tokens_num)
    return prompt


def make_tool_specification(tools, lang="en"):
    functions = [transform_to_openai_function(t) for t in tools]

    commands, cnt = [], 1
    for f in functions:
        func_str = json.dumps(f, ensure_ascii=False)
        commands.append(f"{cnt}:{func_str}")
        cnt += 1

    used_commands = "\n".join(commands)

    tool_spec = f'Commands:\n{used_commands}\n'

    return tool_spec


def make_task_conclusion_prompt(agent_profile, goal, memory, max_tokens_num, tokenizer, lang="en"):
    template = conclusion_prompt_template if lang == "zh" else conclusion_prompt_template_en
    prompt = template.format(**{
        "agent_name": agent_profile.name,
        "agent_bio": agent_profile.bio,
        "agent_instructions": agent_profile.instructions,
        "current_date_and_time": get_current_time_and_date(lang),
        "memory": memory,
        "goal": goal
    })
    prompt = prompt_truncate(tokenizer, prompt, memory, max_tokens_num)
    return prompt


def make_no_task_conclusion_prompt(query, conversation_history=""):
    prompt = ""
    if conversation_history:
        for tmp in conversation_history[-3:]:
            prompt += f"User: {tmp['query']}\nAssistant:{tmp['answer']}\n"
        prompt += f"User: {query}\nAssistant:"
    else:
        prompt = query
    return prompt


def prompt_truncate(tokenizer, prompt, memory, input_max_length):
    kwargs = dict(add_special_tokens=False)
    prompt_tokens = tokenizer.encode(prompt, **kwargs)
    if len(prompt_tokens) > input_max_length:
        if memory is None or memory not in prompt:
            prompt_tokens = prompt_tokens[:input_max_length//2] + prompt_tokens[-input_max_length//2:]
        else:
            memory_prompt_tokens = tokenizer.encode(memory, add_special_tokens=False)
            sublst_len = len(memory_prompt_tokens)
            start_index = None
            for i in range(len(prompt_tokens) - sublst_len + 1):
                if prompt_tokens[i:i+sublst_len] == memory_prompt_tokens:
                    start_index = i
                    break
            
            if start_index is None:
                prompt_tokens = prompt_tokens[:input_max_length//2] + prompt_tokens[-input_max_length//2:]
            else:
                other_len = len(prompt_tokens) -  sublst_len
                if input_max_length > other_len:
                    max_memory_len = input_max_length - other_len
                    memory_prompt_tokens = memory_prompt_tokens[:max_memory_len//2] + memory_prompt_tokens[-max_memory_len//2:]
                    prompt_tokens = prompt_tokens[:start_index] + memory_prompt_tokens + prompt_tokens[start_index + sublst_len:]
    prompt = tokenizer.decode(prompt_tokens, skip_special_tokens=True)
    return prompt