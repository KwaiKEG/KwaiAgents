from __future__ import annotations
import time
import traceback

from kwaiagents.config import CFG
from kwaiagents.llms.clients import OpenAIClient, FastChatClient


def create_chat_completion(
    query: str,
    history: list[tuple[str, str]] = list(),
    system: str = "",
    llm_model_name: str = "gpt-3.5-turbo",
    temperature: float = CFG.temperature,
    max_tokens: int = None,
    stop: str = "",
    chat_id: str = None
) -> tuple[str, list[tuple[str, str]]]:
    if CFG.use_local_llm:
        llm_bot = FastChatClient(llm_model_name.lower(), host=CFG.local_llm_host, port=CFG.local_llm_port)
    else:
        llm_bot = OpenAIClient(llm_model_name.lower())
    response = None
    num_retries = CFG.llm_max_retries
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response, new_history = llm_bot.chat(
                query=query,
                history=history,
                system=system,
                temperature=temperature,
                stop=stop,
                chat_id=chat_id
            )
            if response and "omitted content" not in response.lower():
                break
            else:
                raise RuntimeError("GPT Chat return empty string, Retrying...")
        except Exception as err:
            print(err)
        time.sleep(backoff)
    if not response:
        raise RuntimeError(f"Failed to get response after {num_retries} retries")

    return response, new_history