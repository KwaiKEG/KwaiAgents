from kwaiagents.tools.base import BaseResult, BaseTool


class NoToolResult(BaseResult):
    @property
    def answer(self):
        return ""

class NoTool(BaseTool):
    """
    Do nothing. Other functions are unsuitable due to inability to determine correct parameters from the query or no matching function exists.

    Args:

    Returns:

    """
    name = "do_nothing"
    zh_name = "不使用工具"
    description = 'Do Nothing: "do_nothing",args:'
    tips = ""

    def __call__(self):
        return NoToolResult({})

class FinishResult(BaseResult):
    @property
    def answer(self):
        return self.json_data["reason"]

class FinishTool(BaseTool):
    """ 
    Indicate task completion without the need for further functions. 
    
    Args:

    Returns:

    """
    name = "task_complete"
    zh_name = "任务完成"
    description = 'Task Complete (Shutdown):"task_complete",args: "reason":"<reason-why-complete-but-not-response-the-objective>"'
    tips = ""

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, reason):
        return FinishResult({
            "reason": reason
        })