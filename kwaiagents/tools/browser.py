from __future__ import annotations
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

from kwaiagents.utils.html_utils import extract_hyperlinks, format_hyperlinks
import kwaiagents.utils.nlp_utils as summary
from kwaiagents.config import Config
from kwaiagents.tools.base import BaseTool, BaseResult
from kwaiagents.utils.selenium_utils import get_pagesource_with_selenium

FILE_DIR = Path(__file__).parent.parent


class BrowseResult(BaseResult):
    @property
    def answer(self):
        s = f"{self.json_data['summary']}"
        return s

    @property
    def prompt_responses(self):
        return self.json_data["prompt_responses"]

class BrowserTool(BaseTool):
    """
    Browse a specific website using the provided URL link. 
    Recommended to use URLs from `web_search` to avoid invalid links.

    Args:
        url (str): The website's URL link.
        question (str): The specific content or topic sought on the website.

    Returns:
        str: The webpage content.
    """
    name = "browse_website"
    zh_name = "网页浏览器"
    description = "Browse Website:\"browse_website\",args:\"url\":\"<url>, \"question\":\"<what_you_want_to_find_on_website>\""
    tips = "Browse a specific website using the provided URL link. Recommended to use URLs from `web_search` to avoid invalid links."

    def __init__(self, cfg=None, *args, **kwargs):
        self.cfg = cfg if cfg else Config()

    def __call__(self, url, question="",  *args, **kwargs):
        summary, urls, prompt_responses = browse_website(url, question, self.cfg)
        return BrowseResult({
            "summary": summary,
            "urls": urls,
            "prompt_responses": prompt_responses
        })


def browse_website(url: str, question: str, cfg: Config = None) -> tuple[str, WebDriver]:
    """Browse a website and return the answer and links to the user

    Args:
        url (str): The url of the website to browse
        question (str): The question asked by the user

    Returns:
        Tuple[str, WebDriver]: The answer and links to the user and the webdriver
    """
    if cfg:
        cfg.chain_logger.put("click", f"Access the website {url} ")
    driver, text = scrape_text_with_selenium(url, cfg)
    add_header(driver)
    summary_text, prompt_responses = summary.summarize_text(url, text, question, driver, cfg)
    links = scrape_links_with_selenium(driver, url)

    # Limit links to 5
    if len(links) > 5:
        links = links[:5]
    close_browser(driver)
    return summary_text, links, prompt_responses

def scrape_text_with_selenium(url: str, cfg: Config = None) -> tuple[WebDriver, str]:
    """Scrape text from a website using selenium

    Args:
        url (str): The url of the website to scrape

    Returns:
        Tuple[WebDriver, str]: The webdriver and the text scraped from the website
    """
    driver, page_source = get_pagesource_with_selenium(url, cfg.selenium_web_browser)
    soup = BeautifulSoup(page_source, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return driver, text


def scrape_links_with_selenium(driver: WebDriver, url: str) -> list[str]:
    """Scrape links from a website using selenium

    Args:
        driver (WebDriver): The webdriver to use to scrape the links

    Returns:
        List[str]: The links scraped from the website
    """
    if not driver:
        return list()
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup, url)

    return format_hyperlinks(hyperlinks)


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    if driver:
        driver.quit()


def add_header(driver: WebDriver) -> None:
    """Add a header to the website

    Args:
        driver (WebDriver): The webdriver to use to add the header

    Returns:
        None
    """
    if driver:
        driver.execute_script(open(f"{FILE_DIR}/js/overlay.js", "r").read())