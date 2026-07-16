from __future__ import annotations

import unittest

from langchain_core.messages import AIMessage, HumanMessage

from services.session_state_store import (
    MemorySessionStateStore,
    deserialize_agent_state,
    serialize_agent_state,
)


class SessionStateStoreTests(unittest.IsolatedAsyncioTestCase):
    def test_agent_state_message_round_trip(self):
        state = {
            "session_id": "s1",
            "user_id": "u1",
            "messages": [
                HumanMessage(content="明天下午三点有女技师吗"),
                AIMessage(content="可以，我帮您查一下。"),
            ],
            "focus_context": {"service_type": "肩颈推拿"},
            "availability_result": {"options": [{"technician_name": "李娜"}]},
            "booking": {"status": "idle", "draft": {}},
            "tool_results": {},
        }

        restored = deserialize_agent_state(serialize_agent_state(state))

        self.assertEqual(restored["messages"][0].content, "明天下午三点有女技师吗")
        self.assertEqual(restored["messages"][1].content, "可以，我帮您查一下。")
        self.assertEqual(restored["focus_context"]["service_type"], "肩颈推拿")
        self.assertEqual(restored["availability_result"]["options"][0]["technician_name"], "李娜")

    async def test_memory_store_set_get_delete(self):
        store = MemorySessionStateStore(ttl_seconds=60)
        state = {
            "session_id": "s1",
            "user_id": "u1",
            "messages": [HumanMessage(content="你好")],
            "focus_context": {},
            "availability_result": {},
            "booking": {"status": "idle"},
            "tool_results": {},
        }

        await store.set("s1", state)
        loaded = await store.get("s1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["session_id"], "s1")
        self.assertEqual(loaded["messages"][0].content, "你好")

        await store.delete("s1")
        self.assertIsNone(await store.get("s1"))

    async def test_memory_store_expires_state(self):
        store = MemorySessionStateStore(ttl_seconds=0)
        await store.set(
            "expired",
            {
                "session_id": "expired",
                "messages": [HumanMessage(content="hi")],
                "booking": {"status": "idle"},
            },
        )

        self.assertIsNone(await store.get("expired"))

    async def test_graph_chat_handler_persists_state_by_session(self):
        import api.graph_chat_handler as graph_chat_handler

        class FakeGraph:
            async def ainvoke(self, state):
                result = dict(state)
                result["final_response"] = f"message_count={len(state.get('messages', []))}"
                return result

        original_graph = graph_chat_handler._graph
        original_store = graph_chat_handler._session_store
        graph_chat_handler._graph = FakeGraph()
        graph_chat_handler._session_store = MemorySessionStateStore(ttl_seconds=60)
        try:
            first = await graph_chat_handler.process_user_input_graph("第一轮", session_id="persist-s1")
            second = await graph_chat_handler.process_user_input_graph("第二轮", session_id="persist-s1")

            self.assertEqual(first["final_response"], "message_count=1")
            self.assertEqual(second["final_response"], "message_count=2")
            self.assertTrue(first["turn_trace"]["trace_id"].startswith("trace_"))
            self.assertEqual(first["turn_trace"]["session_id"], "persist-s1")
            self.assertEqual(first["turn_trace"]["user_input"], "第一轮")
            self.assertGreaterEqual(first["turn_trace"]["latency_ms"], 0)
            self.assertEqual(len(first["trace_history"]), 1)
            self.assertEqual(len(second["trace_history"]), 2)

            await graph_chat_handler.reset_graph_session("persist-s1")
            reset_state = await graph_chat_handler.get_graph_session_state("persist-s1")
            self.assertEqual(reset_state, {})
        finally:
            graph_chat_handler._graph = original_graph
            graph_chat_handler._session_store = original_store


if __name__ == "__main__":
    unittest.main()
