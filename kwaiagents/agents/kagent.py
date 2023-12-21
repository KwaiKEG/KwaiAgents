from collections import deque
import json
import logging
import re
import sys
import time
import traceback
from typing import Dict, List
import uuid
from datetime import datetime
from lunar_python import Lunar, Solar
from transformers import AutoTokenizer

from kwaiagents.tools import ALL_NO_TOOLS, ALL_TOOLS, FinishTool, NoTool
from kwaiagents.llms import create_chat_completion
from kwaiagents.agents.prompts import make_planning_prompt
from kwaiagents.agents.prompts import make_no_task_conclusion_prompt, make_task_conclusion_prompt
from kwaiagents.utils.chain_logger import *
from kwaiagents.utils.json_fix_general import find_json_dict, correct_json
from kwaiagents.utils.date_utils import get_current_time_and_date


class SingleTaskListStorage:
    def __init__(self):
        self.tasks = deque([])
        self.task_id_counter = 0

    def append(self, task: Dict):
        self.tasks.append(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def next_task_id(self):
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        return [t["task_name"] for t in self.tasks]
    
    def get_tasks(self):
        return list(self.tasks)

    def clear(self):
        del self.tasks
        self.tasks = deque([])
        self.task_id_counter = 0


class KAgentSysLite(object):
    def __init__(self, cfg, session_id=None, agent_profile=None, lang="en"):
        self.cfg = cfg
        self.agent_profile = agent_profile
        self.lang = lang
        self.max_task_num = agent_profile.max_iter_num
        self.session_id = session_id if session_id else str(uuid.uuid1())
        self.tokenizer = self.initialize_tokenizer(self.cfg.fast_llm_model)

        self.initialize_logger()
        self.initialize_memory()
        self.tool_retrival()

    def initialize_logger(self):
        self.chain_logger = ChainMessageLogger(output_streams=[sys.stdout], lang=self.lang)
        self.cfg.set_chain_logger(self.chain_logger)

    def initialize_memory(self):
        pass
    
    def initialize_tokenizer(self, llm_name):
        if "baichuan" in llm_name:
            model_name = "kwaikeg/kagentlms_baichuan2_13b_mat"
        elif "qwen" in llm_name:
            model_name = "kwaikeg/kagentlms_qwen_7b_mat"
        else:
            model_name = "gpt2"
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=False,
            padding_side='left',
            trust_remote_code=True
        )
        return tokenizer

    def tool_retrival(self):
        if "notool" in self.agent_profile.tools:
            self.tools = list()
        else:
            all_tools = [tool_cls(cfg=self.cfg) for tool_cls in ALL_TOOLS]

            if "auto" in self.agent_profile.tools:
                used_tools = [tool_cls(cfg=self.cfg) for tool_cls in ALL_TOOLS]
            else:
                used_tools = list()
                for tool in all_tools:
                    if tool.zh_name in self.agent_profile.tools or tool.name in self.agent_profile.tools:
                        used_tools.append(tool)
            used_tools += [tool_cls(cfg=self.cfg) for tool_cls in ALL_NO_TOOLS]
            
        self.tools = used_tools
        self.name2tools = {t.name: t for t in self.tools}

    def memory_retrival(self, 
        goal: str, 
        conversation_history: List[List], 
        complete_task_list: List[Dict]):

        memory = ""
        if conversation_history:
            memory += f"* Conversation History:\n"
            for tmp in conversation_history[-3:]:
                memory += f"User: {tmp['query']}\nAssistant:{tmp['answer']}\n"

        if complete_task_list:
            complete_task_str = json.dumps(complete_task_list, ensure_ascii=False, indent=4)
            memory += f"* Complete tasks: {complete_task_str}\n"
        return memory

    def task_plan(self, goal, memory):
        prompt = make_planning_prompt(self.agent_profile, goal, self.tools, memory, self.cfg.max_tokens_num, self.tokenizer, lang=self.lang)
        # print(f'\n************** TASK PLAN AGENT PROMPT *************')
        # print(prompt)
        try:
            response, _ = create_chat_completion(
            query=prompt, llm_model_name=self.cfg.smart_llm_model)
            self.chain_logger.put_prompt_response(
                prompt=prompt, 
                response=response, 
                session_id=self.session_id, 
                mtype="auto_task_create",
                llm_name=self.cfg.smart_llm_model)
            response = correct_json(find_json_dict(response))
            task = json.loads(response)
            new_tasks = [task]
        except:
            print(traceback.format_exc())
            print("+" + response)
            self.chain_logger.put("fail", logging_think_fail_msg(self.lang))
            new_tasks = list()
        
        return new_tasks

    def tool_use(self, command) -> str:
        try:
            command_name = command.get("name", "")
            if command_name == "search":
                command_name = "web_search"
            args_text = ",".join([f'{key}={val}' for key, val in command["args"].items()])
            execute_str = f'{command_name}({args_text})'.replace("wikipedia(", "kuaipedia(")
            self.chain_logger.put("execute", execute_str)
            if not command_name:
                raise RuntimeError("{} has no tool name".format(command))
            if command_name not in self.name2tools:
                raise RuntimeError("has no tool named {}".format(command_name))
            tool = self.name2tools[command_name]

            tool_output = tool(**command["args"])
            self.chain_logger.put("observation", tool_output.answer_md)

            for prompt, response in tool_output.prompt_responses:
                self.chain_logger.put_prompt_response(
                    prompt=prompt,
                    response=response,
                    session_id=self.session_id,
                    mtype=f"auto_command_{command_name}",
                    llm_name=self.cfg.fast_llm_model
                )
            return tool_output.answer
        except KeyboardInterrupt:
            exit()
        except:
            print(traceback.format_exc())
            self.chain_logger.put("observation", logging_execute_fail_msg(self.lang))
            return ""

    def conclusion(self, 
        goal: str, 
        memory,
        conversation_history: List[List],
        no_task_planned: bool = False
        ):

        if no_task_planned:
            prompt = make_no_task_conclusion_prompt(goal, conversation_history)
        else:
            prompt = make_task_conclusion_prompt(self.agent_profile, goal, memory, self.cfg.max_tokens_num, self.tokenizer, lang=self.lang)
        # print(f'\n************** CONCLUSION AGENT PROMPT *************')
        # print(prompt)

        response, _ = create_chat_completion(
            query=prompt, 
            chat_id="kwaiagents_answer_" + self.session_id, 
            llm_model_name=self.cfg.smart_llm_model)

        # print(response)

        self.chain_logger.put_prompt_response(
            prompt=prompt, 
            response=response, 
            session_id=self.session_id, 
            mtype="auto_conclusion",
            llm_name=self.cfg.smart_llm_model)
        return response

    def check_task_complete(self, task, iter_id):
        command_name = task["command"]["name"]
        if not task or ("task_name" not in task) or ("command" not in task) \
            or ("args" not in task["command"]) or ("name" not in task["command"]):
            self.chain_logger.put("finish", str(task.get("task_name", "")))
            return True
        elif command_name == FinishTool.name:
            self.chain_logger.put("finish", str(task["command"]["args"].get("reason", "")))
            return True
        elif command_name == NoTool.name:
            if iter_id == 1:
                self.chain_logger.put("finish", logging_do_not_need_use_tool_msg(self.lang))
            else:
                self.chain_logger.put("finish", logging_do_not_need_use_tool_anymore_msg(self.lang))
            return True
        elif command_name not in self.name2tools:
            self.chain_logger.put("finish", logging_do_not_need_use_tool_msg(self.lang))
            return True
        else:
            return False

    def chat(self, query, history=list(), initial_task_name=None, *args, **kwargs):
        goal = query

        if not self.tools:
            no_task_planned = True
        else:
            tasks_storage = SingleTaskListStorage()
            tasks_storage.clear()

            start = True
            loop = True
            iter_id = 0
            complete_task_list = list()
            no_task_planned = False
            while loop:
                iter_id += 1
                if start or not tasks_storage.is_empty():
                    start = False
                    if not tasks_storage.is_empty():
                        task = tasks_storage.popleft()
                        
                        if (self.check_task_complete(task, iter_id,)):
                            if iter_id <= 2:
                                no_task_planned = True
                            break

                        self.chain_logger.put("thought", task.get("task_name", ""))

                        result = self.tool_use(task["command"])

                        task["result"] = result
                        complete_task_list.append(task)

                    if iter_id > self.agent_profile.max_iter_num:
                        self.chain_logger.put("finish", logging_stop_thinking_msg(self.lang))
                        break
                    self.chain_logger.put("thinking")
                    memory = self.memory_retrival(goal, history, complete_task_list)
                    new_tasks = self.task_plan(goal, memory)

                    for new_task in new_tasks:
                        new_task.update({"task_id": tasks_storage.next_task_id()})
                        tasks_storage.append(new_task)
                else:
                    loop = False
                    self.chain_logger.put("finish", logging_finish_task_msg(self.lang))

        memory = self.memory_retrival(goal, history, complete_task_list)
        self.chain_logger.put("conclusion", "")

        conclusion = self.conclusion(
            goal, 
            memory=memory,
            conversation_history=history,
            no_task_planned=no_task_planned)
        self.chain_logger.put("chain_end", "")

        new_history = history[:] + [{"query": query, "answer": conclusion}]

        return {
            "response": conclusion,
            "history": new_history,
            "chain_msg": self.chain_logger.chain_msgs,
            "chain_msg_str": self.chain_logger.chain_msgs_str,
            "more_info": {},
        }
