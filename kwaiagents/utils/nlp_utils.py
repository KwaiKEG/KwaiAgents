import json
import re
"""Text processing functions"""
from typing import Generator, Optional, Dict
from selenium.webdriver.remote.webdriver import WebDriver
from kwaiagents.config import Config
from kwaiagents.llms import create_chat_completion


def split_sentences(text, lang='en'):
    if not text:
        return []
    if lang == 'en':
        # Split English sentences using regular expression
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    elif lang.startswith('zh'):
        # Split Chinese sentences using regular expression
        sentences = re.split(r'(?<=[。！？])\s*', text)
    else:
        raise ValueError("Unsupported language. Please use 'en' for English or 'zh' for Chinese.")

    # Remove any empty strings from the list
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def split_text(text: str, max_length: int = 4096) -> Generator[str, None, None]:
    """Split text into chunks of a maximum length

    Args:
        text (str): The text to split
        max_length (int, optional): The maximum length of each chunk. Defaults to 8192.

    Yields:
        str: The next chunk of text

    Raises:
        ValueError: If the text is longer than the maximum length
    """
    paragraphs = text.split("\n")
    current_length = 0
    current_chunk = []

    for paragraph in paragraphs:
        if current_length + len(paragraph) + 1 <= max_length:
            current_chunk.append(paragraph)
            current_length += len(paragraph) + 1
        else:
            yield "\n".join(current_chunk)
            current_chunk = [paragraph]
            current_length = len(paragraph) + 1

    if current_chunk:
        yield "\n".join(current_chunk)


def summarize_text(
    url: str, text: str, question: str, driver: Optional[WebDriver] = None, cfg: Config = None
) -> str:
    """Summarize text using the OpenAI API

    Args:
        url (str): The url of the text
        text (str): The text to summarize
        question (str): The question to ask the model
        driver (WebDriver): The webdriver to use to scroll the page
        cfg (Config): The config of the global agent

    Returns:
        str: The summary of the text
    """
    if not text:
        return "Error: No text to summarize", []

    text_length = len(text)
    cfg.chain_logger.put("reading", f"共 {text_length} 字需要阅读")

    summaries = []
    chunks = list(split_text(text, cfg.browse_chunk_max_length))
    scroll_ratio = 1 / len(chunks)

    prompt_responses = list()

    if cfg.fast_llm_model in ["llama"] and len(chunks) > 1:
        batch_size = 3
        cnt = 0
        for i in range(len(chunks) // batch_size + 1):
            if driver:
                scroll_to_percentage(driver, scroll_ratio * i)
            batch_chunk = chunks[i * batch_size: (i + 1) * batch_size]
            if not batch_chunk:
                break
            batch = [
                create_message(chunk, question)
                for chunk in batch_chunk
            ]
            batch_summaries, _ = create_chat_completion(
                    query=batch,
                    llm_model_name=cfg.fast_llm_model,
                    max_tokens=cfg.browse_summary_max_token,
                )
            if isinstance(batch_summaries, str):
                batch_summaries = json.loads(batch_summaries)
            summaries.extend(batch_summaries)

            cnt += len(batch)
            cfg.chain_logger.put("reading", f"{cnt} / {len(chunks)} 个段落")
    else:
        for i, chunk in enumerate(chunks):
            if driver:
                scroll_to_percentage(driver, scroll_ratio * i)
            # print(f"Adding chunk {i + 1} / {len(chunks)} to memory")

            # memory_to_add = f"Source: {url}\n" f"Raw content part#{i + 1}: {chunk}"

            # MEMORY.add(memory_to_add)


            cfg.chain_logger.put("reading", f"第 {i + 1} / {len(chunks)} 个段落")
            message = create_message(chunk, question)

            try:
                summary, _ = create_chat_completion(
                    query=message,
                    llm_model_name=cfg.fast_llm_model,
                    max_tokens=cfg.browse_summary_max_token,
                )
            except:
                summary = ""
            summaries.append(summary)
            
            prompt_responses.append((message, summary))
        # print(f"Added chunk {i + 1} summary to memory")

        # memory_to_add = f"Source: {url}\n" f"Content summary part#{i + 1}: {summary}"

        # MEMORY.add(memory_to_add)
    print(len(summaries))
    if len(summaries) == 1:
        return summary, prompt_responses
    if len(summaries) == 0:
        return "", prompt_responses
    cfg.chain_logger.put("reading", f"总结这 {len(chunks)} 个段落")
    print(f"Summarized {len(chunks)} chunks.")

    combined_summary = "\n".join(summaries)
    message = create_message(combined_summary, question)

    summary, _ = create_chat_completion(
            query=message,
            llm_model_name=cfg.fast_llm_model,
            max_tokens=cfg.browse_summary_max_token,
        )
    prompt_responses.append((message, summary))

    return summary, prompt_responses


def scroll_to_percentage(driver: WebDriver, ratio: float) -> None:
    """Scroll to a percentage of the page

    Args:
        driver (WebDriver): The webdriver to use
        ratio (float): The percentage to scroll to

    Raises:
        ValueError: If the ratio is not between 0 and 1
    """
    if ratio < 0 or ratio > 1:
        raise ValueError("Percentage should be between 0 and 1")
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio});")


def create_message(chunk: str, question: str) -> Dict[str, str]:
    """Create a message for the chat completion

    Args:
        chunk (str): The chunk of text to summarize
        question (str): The question to answer

    Returns:
        Dict[str, str]: The message to send to the chat completion
    """
    return f'"""{chunk}""" 基于上述文本回答下面的问题 ' +\
        f'问题: "{question}" -- 假如无法回答这个问题，则总结上述文本：'


if __name__ == "__main__":
    # Example usage
    text_en = "This is an example sentence. Here's another one! And a third?"
    text_zh = "这是一个示例句子。这是另一个！还有第三个？"

    sentences_en = split_sentences(text_en, lang='en')
    sentences_zh = split_sentences(text_zh, lang='zh')

    print(sentences_en)
    print(sentences_zh)