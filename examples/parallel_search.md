# Parallel web search as a custom tool

Use [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
to give KAgentSys-Lite an optional web search tool with source URLs and excerpts.
Anonymous search uses Fast mode and needs no Parallel account or API key. The
free endpoint has usage limits and is intended for exploration and light use.
The existing DuckDuckGo search and other built-in tools stay unchanged.

## Install and try a search

Use Python 3.10 or newer. From the repository root, install KwaiAgents and the
example's optional dependencies in your environment:

```bash
python -m pip install -e .
python -m pip install -r examples/requirements-parallel.txt
python -m examples.parallel_search_example --query "Python latest stable release"
```

This command invokes the search tool directly and prints the returned text,
including source URLs. It requires network access to `https://search.parallel.ai/mcp`
but no LLM service, browser driver, or model weights. Network errors, service
errors and calls exceeding the 60-second timeout raise an exception.

## Add it to your agent

Pass the class through the same `tools` argument used by the
[custom-tool example](custom_tool_example.py). For example, after configuring
your LLM service as described in the main README:

```python
from examples.parallel_search_example import ParallelSearchTool
from kwaiagents.agents import AgentProfile, KAgentSysLite
from kwaiagents.config import Config
from kwaiagents.tools import ALL_NO_TOOLS

cfg = Config()
cfg.fast_llm_model = "gpt-3.5-turbo"
cfg.smart_llm_model = "gpt-3.5-turbo"
profile = AgentProfile({"lang": "en"})
agent = KAgentSysLite(
    cfg=cfg,
    agent_profile=profile,
    tools=[ParallelSearchTool] + ALL_NO_TOOLS,
    lang="en",
)
agent.chat("Find the latest stable Python release and cite its release page.", history=[])
```

The planner sees `parallel_web_search(text)` and receives search excerpts as
tool observations. This explicit tool list selects Parallel search along with
the agent's finish/no-tool commands for this agent only. To keep other tools,
include their classes in the list too. The ordinary `kagentsys` CLI does not
register this example automatically. Agent use still requires your configured
LLM service and its normal tokenizer setup.

The tool uses MCP Streamable HTTP, keeps one search session identifier per tool
instance, and does not read a Parallel API key from your environment. Reuse the
agent for related turns and create a new agent for a new conversation. It is a
synchronous custom tool; call it outside an already running asyncio event loop.

## Check the example

```bash
python -m unittest discover -s tests -p 'test_parallel_search_example.py'
```
