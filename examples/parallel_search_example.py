"""Opt-in Parallel Search MCP tool for KAgentSys-Lite."""

import argparse
import asyncio
from html import escape
import uuid

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from kwaiagents.tools.base import BaseResult, BaseTool


MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "KwaiAgents-Parallel-Example/0.1"


class ParallelSearchResult(BaseResult):
    @property
    def answer(self):
        return self.json_data["text"]

    @property
    def answer_md(self):
        # Remote excerpts are untrusted text, including any embedded HTML.
        return "<pre>" + escape(self.answer) + "</pre>"


class ParallelSearchTool(BaseTool):
    """Search the web for current information using Parallel.

    Args:
        text (str): A focused search query, preferably 3-6 keywords.

    Returns:
        str: Search results with source URLs and relevant excerpts.
    """

    name = "parallel_web_search"
    zh_name = "Parallel网页搜索"
    description = 'Parallel Search:"parallel_web_search",args:"text":"<search>"'
    tips = ""

    def __init__(self, cfg=None, timeout=60, *args, **kwargs):
        self.timeout = timeout
        self.session_id = str(uuid.uuid4())

    async def _search(self, text):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=self.timeout
        ) as client:
            async with streamable_http_client(MCP_URL, http_client=client) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    result = await session.call_tool("web_search", {
                        "objective": text,
                        "search_queries": [text],
                        "session_id": self.session_id,
                    })
        content = "\n".join(
            block.text for block in result.content if block.type == "text"
        )
        if result.isError:
            raise RuntimeError("Parallel search failed: " + content)
        if not content.strip():
            raise RuntimeError("Parallel search returned no text content")
        return ParallelSearchResult({"text": content})

    def __call__(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Search text must be a nonempty string")
        # KAgentSys-Lite invokes custom tools synchronously. Bound the entire
        # connection and tool call, and let failures reach its error handler.
        async def search_with_timeout():
            return await asyncio.wait_for(self._search(text), timeout=self.timeout)

        return asyncio.run(search_with_timeout())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()
    print(ParallelSearchTool()(args.query).answer)
