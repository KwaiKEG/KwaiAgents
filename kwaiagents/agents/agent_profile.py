import json


_profile_default_name_fn = lambda x: "AI助手" if x == "zh" else "AI Assitant"
_profile_default_bio_fn = lambda x: "你能帮助人类解决他们的问题" if x == "zh" else "You can help people solve their problems"
_profile_default_instruct_pre_fn = lambda x: "你要遵循以下指令行动：\n" if x == "zh" else "You should follow these following instructions:\n"


class AgentProfile(object):
    def __init__(self, input_dict: dict = None):
        self.input_dict = input_dict
        self.lang = input_dict.get("lang", "en")
        self.from_json(input_dict)

    def from_json(self, input_dict):
        self.name = input_dict.get("agent_name", "")
        if not self.name:
            self.name = _profile_default_name_fn(self.lang)
        self.bio = input_dict.get("agent_bio", "")
        if not self.bio:
            self.bio = _profile_default_bio_fn(self.lang)
        self.max_iter_num = int(input_dict.get("max_iter_num", 5))
        self.instructions = input_dict.get("agent_instructions", "")
        if self.instructions:
            self.instructions = _profile_default_instruct_pre_fn(self.lang) + self.instructions
        tool_names = input_dict.get("tool_names", '["auto"]')
        if isinstance(tool_names, str):
            self.tools = json.loads(tool_names)
        else:
            self.tools = tool_names

    def to_json_file(self, fname):
        with open(fname, "w") as f:
            json.dump({k:v for k, v in self.__dict__.items()},f, ensure_ascii=False, indent=2)

    def __str__(self):
        s = "============ Agent Profile ============\n"
        for key, val in self.__dict__.items():
            if key == "input_dict":
                continue
            s += f"· {key.upper()}:\t{val}\n"
        return s
