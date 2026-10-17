import asyncio
from contextlib import contextmanager, redirect_stdout
import io
import json
import unittest
from unittest.mock import patch

import httpx

from examples import parallel_search_example as example
from kwaiagents.agents import AgentProfile, KAgentSysLite
from kwaiagents.config import Config
from kwaiagents.tools import ALL_NO_TOOLS, ALL_TOOLS, FinishTool
from kwaiagents.utils.function_utils import transform_to_openai_function


EXCERPT = "Python release: https://www.python.org/downloads/ <script>alert(1)</script>"
ASYNC_CLIENT = httpx.AsyncClient


class SearchExampleTests(unittest.TestCase):
    @contextmanager
    def server(self, tool_error=False, empty=False, slow=False):
        requests = []
        clients = []

        async def handle(request):
            requests.append(request)
            if request.method != "POST":
                return httpx.Response(405)
            message = json.loads(request.content)
            if "id" not in message:
                return httpx.Response(202)
            if message["method"] == "initialize":
                result = {
                    "protocolVersion": message["params"]["protocolVersion"],
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "test-search", "version": "1"},
                }
            elif message["method"] == "tools/list":
                result = {"tools": [{
                    "name": "web_search",
                    "inputSchema": {"type": "object", "properties": {}},
                }]}
            elif message["method"] == "tools/call":
                if slow:
                    await asyncio.sleep(10)
                result = {
                    "content": [] if empty else [{"type": "text", "text": EXCERPT}],
                    "isError": tool_error,
                }
            else:
                raise AssertionError(message)
            return httpx.Response(200, json={
                "jsonrpc": "2.0", "id": message["id"], "result": result,
            })

        def client(**kwargs):
            instance = ASYNC_CLIENT(transport=httpx.MockTransport(handle), **kwargs)
            clients.append(instance)
            return instance

        with patch.object(example.httpx, "AsyncClient", side_effect=client):
            yield requests, clients

    def make_agent(self):
        with patch.object(KAgentSysLite, "initialize_tokenizer", return_value=None):
            return KAgentSysLite(
                Config(), agent_profile=AgentProfile({"lang": "en"}),
                tools=[example.ParallelSearchTool] + ALL_NO_TOOLS,
            )

    def test_native_loader_dispatch_and_request_contract(self):
        defaults = tuple(ALL_TOOLS)
        with self.server() as (requests, clients), redirect_stdout(io.StringIO()):
            agent = self.make_agent()
            for _ in range(2):
                answer = agent.tool_use({
                    "name": "parallel_web_search", "args": {"text": "Python latest release"},
                })
                self.assertEqual(answer, EXCERPT)
            calls = [json.loads(r.content) for r in requests if r.method == "POST"]
            calls = [m for m in calls if m.get("method") == "tools/call"]
            self.assertEqual(len(calls), 2)
            for call in calls:
                self.assertEqual(call["params"]["name"], "web_search")
                self.assertEqual(call["params"]["arguments"], {
                    "objective": "Python latest release",
                    "search_queries": ["Python latest release"],
                    "session_id": agent.name2tools["parallel_web_search"].session_id,
                })
            for request in requests:
                self.assertEqual(str(request.url), example.MCP_URL)
                self.assertEqual(request.headers["user-agent"], example.USER_AGENT)
                self.assertNotIn("authorization", request.headers)
            self.assertTrue(all(c.is_closed for c in clients))
            self.assertEqual(tuple(ALL_TOOLS), defaults)
            self.assertNotIn(example.ParallelSearchTool, ALL_TOOLS)
            self.assertIn(FinishTool.name, agent.name2tools)
            schema = transform_to_openai_function(agent.name2tools["parallel_web_search"])
            self.assertEqual(schema["required"], ["text"])

    def test_agent_loop_consumes_search_observation(self):
        plans = [
            [{"task_name": "Search", "command": {
                "name": "parallel_web_search", "args": {"text": "Python latest release"},
            }}],
            [{"task_name": "Done", "command": {"name": FinishTool.name, "args": {}}}],
        ]
        with self.server(), redirect_stdout(io.StringIO()):
            agent = self.make_agent()
            with patch.object(agent, "task_plan", side_effect=plans), \
                    patch.object(agent, "conclusion", return_value="Answer") as conclude:
                result = agent.chat("Find Python releases", history=[])
            self.assertEqual(result["response"], "Answer")
            self.assertIn(EXCERPT, conclude.call_args.kwargs["memory"])

    def test_untrusted_html_is_escaped(self):
        result = example.ParallelSearchResult({"text": EXCERPT})
        self.assertEqual(result.answer, EXCERPT)
        self.assertNotIn("<script>", result.answer_md)
        self.assertIn("&lt;script&gt;", result.answer_md)

    def test_service_errors_and_empty_responses_are_not_success(self):
        for options in ({"tool_error": True}, {"empty": True}):
            with self.subTest(options=options), self.server(**options):
                with self.assertRaises(RuntimeError):
                    example.ParallelSearchTool()("Python latest release")

    def test_timeout_closes_transport(self):
        with self.server(slow=True) as (_, clients):
            with self.assertRaises(asyncio.TimeoutError):
                example.ParallelSearchTool(timeout=0.05)("Python latest release")
            self.assertTrue(all(c.is_closed for c in clients))

    def test_cancellation_propagates_and_closes_transport(self):
        async def cancel_search():
            with self.server(slow=True) as (requests, clients):
                task = asyncio.create_task(example.ParallelSearchTool()._search("Python release"))
                for _ in range(100):
                    if any(b'tools/call' in r.content for r in requests if r.method == "POST"):
                        break
                    await asyncio.sleep(0.001)
                else:
                    self.fail("Search request was never dispatched")
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                self.assertTrue(all(c.is_closed for c in clients))

        asyncio.run(cancel_search())

    def test_blank_input_sends_no_request(self):
        with self.server() as (requests, _):
            with self.assertRaises(ValueError):
                example.ParallelSearchTool()(" ")
            self.assertEqual(requests, [])


if __name__ == "__main__":
    unittest.main()
