import os

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import logging

import time


def get_web_driver(selenium_web_browser):
    options_available = {
        "chrome": ChromeOptions,
        "safari": SafariOptions,
        "firefox": FirefoxOptions,
    }

    options = options_available[selenium_web_browser]()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
    )
    
    if selenium_web_browser == "firefox":
        current_driver = webdriver.Firefox(
            executable_path=GeckoDriverManager().install(), options=options
        )
    elif selenium_web_browser == "safari":
        # Requires a bit more setup on the users end
        # See https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
        current_driver = webdriver.Safari(options=options)
    else:
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        proxy = os.getenv("http_proxy")
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        current_driver = webdriver.Chrome(options=options)
    return current_driver


def get_pagesource_with_selenium(url: str, selenium_web_browser:str, driver: WebDriver = None) -> str:
    logging.getLogger("selenium").setLevel(logging.CRITICAL)
    driver = get_web_driver(selenium_web_browser)
    if driver is None:
        driver = get_web_driver(selenium_web_browser)
    
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Get the HTML content directly from the browser's DOM
    page_source = driver.execute_script("return document.body.outerHTML;")
    return driver, page_source