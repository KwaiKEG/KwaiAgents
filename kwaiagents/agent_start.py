import argparse
from datetime import datetime
import json
import os
import sys
import time
import traceback
from kwaiagents.config import Config, CFG
from kwaiagents.agents import KAgentSysLite, AgentProfile


class AgentService(object):
    def __init__(self, *args, **kwargs):
        self.cfg = Config()
        self.agent_profile = None
        self.p_date = datetime.today().strftime('%Y%m%d')

    @staticmethod
    def parse_config(input_dict):
        cfg = Config()

        llm_name = input_dict.get("llm_name", "").lower()
        cfg.fast_llm_model = llm_name
        cfg.smart_llm_model = llm_name
        cfg.max_tokens_num = input_dict.get("max_tokens_num", 4096)
        if llm_name == "gpt-4":
            cfg.fast_llm_model = "gpt-3.5-turbo"

        return cfg

    @staticmethod
    def load_history(input_dict):
        history = input_dict.get("history", list())
        if not history:
            history = list()
        if isinstance(history, str):
            history = json.loads(history)
        return history

    def chat(self, input_dict):
        s = "============ INPUT_DICT ============\n"
        for key, val in input_dict.items():
            s += f"· {key.upper()}:\t{val}\n"
        print(s)

        chat_id = str(input_dict["id"])
        history = self.load_history(input_dict)
        self.cfg = self.parse_config(input_dict)
        self.agent_profile = AgentProfile(input_dict)

        print(self.cfg)
        print(self.agent_profile)

        try:
            agent = KAgentSysLite(
                    cfg=self.cfg,
                    session_id=chat_id,
                    agent_profile=self.agent_profile,
                    lang=input_dict.get("lang", "en"))

            print("\033[95m\033[1m" + "\n***** Question *****" + "\033[0m\033[0m")
            print(input_dict["query"])

            agent_results = agent.chat(
                input_dict["query"], 
                history=history)

            print("\033[95m\033[1m" + "\n***** Response *****" + "\033[0m\033[0m")
            print(agent_results["response"])

            result = {
                "id": chat_id,
                "response": agent_results["response"],
                "history": json.dumps(agent_results["history"], ensure_ascii=False),
                "chain_msg": agent_results["chain_msg"],
                "chain_msg_str": agent_results["chain_msg_str"],
                "more_info": agent_results["more_info"]
            }

        except KeyboardInterrupt:
            exit()
        except:
            print(traceback.format_exc())
            result = {
                "id": chat_id,
                "response": "error"
            }

        return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", type=str, default="test", help="ID of this conversation")
    parser.add_argument("--query", type=str, required=True, help="User query")
    parser.add_argument("--history", type=str, default='[]', help="History of conversation")
    parser.add_argument("--llm_name", type=str, default="gpt-3.5-turbo", help="the name of llm")
    parser.add_argument("--use_local_llm", default=False, action='store_true', help="Whether to use local llm")
    parser.add_argument("--local_llm_host", type=str, default="localhost", help="The host of local llm service")
    parser.add_argument("--local_llm_port", type=int, default="8888", help="The port of local llm service")

    parser.add_argument("--tool_names", type=str, default='["auto"]', help="the name of llm")
    parser.add_argument("--max_iter_num", type=int, default=1, help="the number of iteration of agents")
    parser.add_argument("--agent_name", type=str, default="", help="The agent name")
    parser.add_argument("--agent_bio", type=str, default="", help="The agent bio, a short description")
    parser.add_argument("--agent_instructions", type=str, default="", help="The instructions of how agent thinking, acting, or talking")
    parser.add_argument("--external_knowledge", type=str, default="", help="The link of external knowledge")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "zh"], help="The language of the overall system")
    parser.add_argument("--max_tokens_num", type=int, default=4096, help="Maximum length of model input")

    args = parser.parse_args()

    CFG.local_llm_host = args.local_llm_host
    CFG.local_llm_port = args.local_llm_port
    CFG.use_local_llm = args.use_local_llm

    agent_service = AgentService()

    agent_service.chat(vars(args))


if __name__ == "__main__":
    main()