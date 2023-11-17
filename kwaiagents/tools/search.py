from itertools import islice
import json
import os
import random
import traceback
from bs4 import BeautifulSoup as soup
from duckduckgo_search import DDGS

from kwaiagents.tools.base import BaseResult, BaseTool
from kwaiagents.utils.selenium_utils import get_pagesource_with_selenium
from kwaiagents.config import Config


class SearchResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            rst = ""
            for item in self.json_data:
                rst += f'title: {item["title"]}\nbody: {item["body"]}\nurl: {item["href"]}\n'
            return rst.strip()

    @property
    def answer_md(self):
        if not self.json_data:
            return ""
        else:
            return "\n" + "\n".join([f'{idx + 1}. <a href="{item["href"]}" target="_blank"><b>{item["title"]}</b></a>' + " | " + item["body"] 
                for idx, item in enumerate(self.json_data)])

    @property
    def answer_full(self):
        if not self.json_data:
            return ""
        else:
            return json.dumps(self.json_data, ensure_ascii=False, indent=2)


class SearchTool(BaseTool):
    """
    Perform an internet search.

    Args:
        text (str): Search query.

    Returns:
        str: Multiple webpage links along with brief descriptions.
    """
    name = "web_search"
    zh_name = "网页搜索"
    description = "Web Search:\"web_search\",args:\"text\":\"<search>\""
    tips = ""
    
    def __init__(self, cfg=None, max_search_nums=5, lang="wt-wt", max_retry_times=5, *args, **kwargs):
        self.cfg = cfg if cfg else Config()
        self.max_search_nums = max_search_nums
        self.max_retry_times = max_retry_times
        self.lang = lang
        self.driver = None
        self.driver_cnt = 0

    def set_driver(self, driver):
        self.driver_cnt += 1
        if self.driver_cnt >= 20:
            self.driver_cnt = 0
            self.driver = None
        else:
            self.driver = driver
            
    def get_results_by_selenium(self, keyword):
        url = f"https://duckduckgo.com/?q={keyword}&t=h_&ia=web"
        driver, page_source = get_pagesource_with_selenium(url, "chrome", self.driver)
        self.set_driver(driver)
        page_soup = soup(page_source, "html.parser")
        articles = page_soup.find_all("article")

        results = list()
        for idx, article in enumerate(articles):
            if idx >= self.max_search_nums:
                break
            href = article.find_all("a")[1]['href']
            title = article.find(class_="EKtkFWMYpwzMKOYr0GYm LQVY1Jpkk8nyJ6HBWKAk").text
            body = article.find(class_="OgdwYG6KE2qthn9XQWFC").text
            results.append({
                "title": title,
                "href": href,
                "body": body
            })
        return results

    def get_results_by_ddg(self, keyword):
        search_results = list()

        my_proxy = os.getenv("http_proxy")
        with DDGS(proxies=my_proxy, timeout=20) as ddgs:
            ddgs_gen = ddgs.text(keyword, backend="api", region='sg-en', timelimit='y')
            for r in islice(ddgs_gen, self.max_search_nums):
                search_results.append(r)
        return search_results

    def _retry_search_result(self, keyword, counter=0):
        counter += 1
        if counter > self.max_retry_times:
            print("Search failed after %d retrying" % counter)
            return [{
                "title": "Search Failed",
                "href": "",
                "body": ""
            }]
        try:
            use_selenium = False
            try:
                search_results = self.get_results_by_ddg(keyword)
            except:
                print(traceback.format_exc())
                use_selenium = True
            if not search_results and counter >= 2:
                use_selenium = True
            if use_selenium:
                search_results = self.get_results_by_selenium(keyword)
            if search_results and ("Google Patents" in search_results[0]["body"] or "patent" in search_results[0]["href"]):
                search_results = list()
            if not search_results:
                return self._retry_search_result(keyword, counter)
            return search_results
        except:
            print(traceback.format_exc())
            print("Retry search...")
            return self._retry_search_result(keyword, counter)
        
    def __call__(self, text):
        return SearchResult(self._retry_search_result(text))