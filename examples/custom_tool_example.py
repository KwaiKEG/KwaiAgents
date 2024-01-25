from datetime import datetime
import json
import requests
from gtrending import fetch_repos
from kwaiagents.tools.base import BaseTool, BaseResult
from kwaiagents.agents import AgentProfile, KAgentSysLite
from kwaiagents.config import Config, CFG


class GithubTrendingResults(BaseResult):
    @property
    def answer(self):
        rst = [
            {
                "author": t["author"],
                "name": t["name"],
                "stars": t["stars"],
                "forks": t["forks"],
                "language": t["language"],
                "description": t["description"].strip()
            } for t in self.json_data["data"]]

        return f'{self.json_data["since"]} Github Trending Results: ' + json.dumps(rst, ensure_ascii=False)
    
    @property
    def answer_md(self):
        rst = ""
        for _, data in enumerate(self.json_data['data']):
            rst += f'''
            <h3> <a href="{data['url']}" target="_blank"> {data['fullname']} </a> ({data["stars"]} stars, {data["forks"]} forks)</h3>
            <p style="color:rgb(90,98,106)"> {data["description"].strip()} </p>'''
        return rst


class GithubTrendingTool(BaseTool):
    """
    Retrieve GitHub trending repositories.

    Args:
        since (str): Time frame, options: 'daily', 'weekly', 'monthly'.

    Returns:
        str: GitHub trending results.
    """
    name = "github_trending"
    zh_name = "Github热榜"
    description = ""
    tips = ""

    def __init__(self, max_item_num=10, *args, **kwargs):
        self.max_item_num = max_item_num
        pass

    def __call__(self, since, *args, **kwargs):
        if since not in ["daily", "weekly", "monthly"]:
            since = "daily"
        return GithubTrendingResults({
            "data": fetch_repos(since=since)[:self.max_item_num],
            "since": since
        })


if __name__ == "__main__":
    input_dict = {
        "lang": "en",
        "llm_name": "kagentlms_qwen_7b_mat",
    }
    agent_profile = AgentProfile(input_dict)
    cfg = Config()

    llm_name = input_dict.get("llm_name", "").lower()
    cfg.fast_llm_model = llm_name
    cfg.smart_llm_model = llm_name

    CFG.local_llm_host = "localhost"
    CFG.local_llm_port = 8888
    CFG.use_local_llm = True

    agent = KAgentSysLite(
            cfg=cfg,
            session_id="test_trending_tools",
            agent_profile=agent_profile,
            tools=[GithubTrendingTool],
            lang=input_dict["lang"])

    agent_results = agent.chat(
            "List hottest repo today.", 
            history=[])