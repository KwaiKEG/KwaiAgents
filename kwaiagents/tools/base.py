import pprint


class BaseResult(object):
    def __init__(self, json_data):
        self.json_data = json_data

    def __str__(self):
        return pprint.pformat(self.json_data)

    @property
    def answer(self):
        return ""

    @property
    def answer_md(self):
        return self.answer

    @property
    def urls(self):
        return list()

    @property
    def prompt_responses(self):
        return list()


class BaseTool(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self):
        return BaseResult({})