import os
import json
from kwaiagents.utils.chain_logger import ChainMessageLogger


class Config(object):
    def __init__(self) -> None:
        """Initialize the Config class"""
        self.fast_llm_model = "gpt-3.5-turbo"
        self.smart_llm_model = "gpt-4"
        self.use_local_llm = False
        self.local_llm_host = "localhost"
        self.local_llm_port = 8888
        self.browse_chunk_max_length = 4096
        self.browse_summary_max_token = 300
        self.selenium_web_browser = "chrome"
        self.llm_max_retries = 5
        self.temperature = 1.0
        self.chain_logger = ChainMessageLogger()

    def __str__(self):
        s = "============ CONFIG ============\n"
        for key, val in self.__dict__.items():
            s +=  "· " + key.upper() + ":\t" + str(val) + '\n'
        return s

    def to_json_file(self, fname):
        with open(fname, "w") as f:
            json.dump({k:v for k, v in self.__dict__.items() if k not in ["chain_logger"]},f, ensure_ascii=False, indent=2)

    def set_chain_logger(self, chain_logger):
        self.chain_logger = chain_logger

CFG = Config()