from __future__ import annotations

from datetime import timedelta
import unittest
from unittest.mock import patch

from langchain_core.messages import HumanMessage

from agents.specialists.booking.actions import (
    booking_match_node,
    booking_parse_node,
    booking_guard_node,
    booking_confirmation_node,
    booking_confirmation_prompt_node,
    booking_missing_node,
)
from agents.supervisor.router_actions import main_router_node
from config.time_config import time_config


class GraphNodeContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_pending_booking_replace_technician_excludes_current_choice(self):
        class FakeParser:
            def __init__(self, model):
                pass

            def parse_stream(self, user_input, history):
                return ["{}"]

            def parse_data(self, content):
                return {
                    "start_time": "未知",
                    "duration": "未知",
                    "project": "未知",
                    "gender": "未知",
                    "preference": "未知",
                    "technician_name": "未知",
                }

        class FakeRecall:
            def recall(self, user_id):
                return {"preferred_technician_name": "赵敏"}

        state = {
            "messages": [HumanMessage(content="我想换一个技师")],
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {
                    "service_type": "全身推拿",
                    "start_time": "2026-06-11 10:00",
                    "duration_minutes": 60,
                    "gender_preference": "女",
                    "technician_name": "赵敏",
                },
                "selected_option": {
                    "technician_id": 4,
                    "technician_name": "赵敏",
                },
            },
        }

        with (
            patch("agents.specialists.booking.actions.InputParser", FakeParser),
            patch("agents.specialists.booking.actions.create_chat_model", lambda temperature=0: object()),
            patch("agents.specialists.booking.actions.PreferenceRecallService", lambda: FakeRecall()),
        ):
            result = await booking_parse_node(state)

        self.assertEqual(result["booking"]["status"], "draft_ready")
        self.assertIsNone(result["booking"]["selected_option"])
        self.assertEqual(result["booking"]["excluded_technician_ids"], [4])
        self.assertNotIn("technician_name", result["booking"]["draft"])
        self.assertTrue(result["tool_results"]["replace_technician"])

    async def test_booking_match_passes_excluded_technicians_to_tool(self):
        captured = {}

        class FakeMatchTool:
            def invoke(self, payload):
                captured.update(payload)
                return {
                    "success": True,
                    "data": {
                        "match_type": "direct",
                        "technician": {"id": 3, "name": "李娜", "gender": "女"},
                    },
                }

        state = {
            "booking": {
                "status": "draft_ready",
                "draft": {
                    "service_type": "全身推拿",
                    "start_time": "2026-06-11 10:00",
                    "duration_minutes": 60,
                    "gender_preference": "女",
                },
                "excluded_technician_ids": [4],
            }
        }

        with patch("agents.specialists.booking.actions.match_technician", FakeMatchTool()):
            result = await booking_match_node(state)

        self.assertEqual(captured["excluded_technician_ids"], [4])
        self.assertEqual(result["booking"]["selected_option"]["technician_name"], "李娜")

    async def test_booking_missing_node_keeps_drafting_and_asks(self):
        state = {
            "booking": {
                "status": "drafting",
                "draft": {"service_type": "按摩"},
                "missing_fields": ["start_time", "duration", "gender"],
            }
        }

        result = await booking_missing_node(state)

        self.assertEqual(result["booking"]["status"], "drafting")
        self.assertEqual(result["booking"]["missing_fields"], ["start_time", "duration", "gender"])
        self.assertIn("[预约机器人]", result["final_response"])
        self.assertIn("messages", result)

    async def test_booking_confirmation_prompt_moves_to_awaiting_confirmation(self):
        state = {
            "booking": {
                "status": "matched",
                "draft": {
                    "service_type": "背部推拿",
                    "start_time": "2026-06-10 15:00",
                    "duration_minutes": 40,
                },
                "selected_option": {
                    "technician_id": 3,
                    "technician_name": "李娜",
                },
            }
        }

        result = await booking_confirmation_prompt_node(state)

        self.assertEqual(result["booking"]["status"], "awaiting_confirmation")
        self.assertIn("请问是否确认预约", result["final_response"])
        self.assertIn("李娜", result["final_response"])

    async def test_booking_confirmation_confirm_sets_confirmed_without_writing(self):
        state = {
            "messages": [HumanMessage(content="确认")],
            "route_decision": {"action": "confirm_booking"},
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {
                    "service_type": "按摩",
                    "start_time": "2026-06-10 15:00",
                    "duration_minutes": 60,
                },
                "selected_option": {
                    "technician_id": 1,
                    "technician_name": "张伟",
                },
            },
        }

        result = await booking_confirmation_node(state)

        self.assertEqual(result["booking"]["status"], "confirmed")
        self.assertNotIn("final_response", result)

    async def test_booking_confirmation_cancel_resets_active_context(self):
        state = {
            "messages": [HumanMessage(content="取消")],
            "route_decision": {"action": "cancel_booking"},
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {"service_type": "按摩"},
                "selected_option": {"technician_id": 1, "technician_name": "张伟"},
            },
            "availability_result": {"criteria_snapshot": {"duration_minutes": 60}},
            "focus_context": {"service_type": "按摩"},
        }

        result = await booking_confirmation_node(state)

        self.assertEqual(result["booking"]["status"], "cancelled")
        self.assertEqual(result["booking"]["draft"], {})
        self.assertEqual(result["availability_result"]["options"], [])
        self.assertIn("已取消", result["final_response"])

    async def test_booking_guard_blocks_outside_booking_window(self):
        outside_window = time_config.today().replace(hour=15, minute=0) + timedelta(days=3)
        state = {
            "booking": {
                "status": "confirmed",
                "draft": {
                    "service_type": "massage",
                    "start_time": time_config.format_datetime(outside_window),
                    "duration_minutes": 60,
                },
                "selected_option": {"technician_id": 1, "technician_name": "tech"},
            }
        }

        result = await booking_guard_node(state)

        self.assertFalse(result["tool_results"]["booking_guard"]["success"])
        self.assertEqual(result["booking"]["guard_result"]["reason"], "outside_booking_window")
        self.assertEqual(result["booking"]["status"], "drafting")

    async def test_booking_guard_blocks_outside_business_hours(self):
        tomorrow_morning = time_config.today().replace(hour=9, minute=30) + timedelta(days=1)
        state = {
            "booking": {
                "status": "confirmed",
                "draft": {
                    "service_type": "massage",
                    "start_time": time_config.format_datetime(tomorrow_morning),
                    "duration_minutes": 60,
                },
                "selected_option": {"technician_id": 1, "technician_name": "tech"},
            }
        }

        result = await booking_guard_node(state)

        self.assertFalse(result["tool_results"]["booking_guard"]["success"])
        self.assertEqual(result["booking"]["guard_result"]["reason"], "outside_business_hours")
        self.assertEqual(result["booking"]["status"], "drafting")

    def test_time_policy_business_hours_and_window(self):
        self.assertEqual(time_config.get_business_hours(), (10, 22))

        tomorrow = time_config.today().replace(hour=10, minute=0) + timedelta(days=1)
        ok, reason = time_config.validate_booking_time(
            tomorrow,
            tomorrow + timedelta(minutes=60),
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")

        late = time_config.today().replace(hour=21, minute=30) + timedelta(days=1)
        ok, reason = time_config.validate_booking_time(
            late,
            late + timedelta(minutes=60),
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "outside_business_hours")

    async def test_service_selection_after_availability_starts_booking(self):
        state = {
            "messages": [HumanMessage(content="我想要做全身推拿")],
            "availability_result": {
                "criteria_snapshot": {
                    "start_time": "2026-06-10 15:00",
                    "gender": "女",
                },
                "options": [{"technician_name": "李娜"}],
            },
            "booking": {"status": "idle"},
        }

        result = await main_router_node(state)

        self.assertEqual(result["route_decision"]["action"], "start_or_continue_booking")
        self.assertEqual(result["route_decision"]["reason"], "service_selection_after_availability")

    async def test_duration_service_refinement_after_availability_stays_availability(self):
        state = {
            "messages": [HumanMessage(content="我想要2小时全身按摩")],
            "availability_result": {
                "criteria_snapshot": {"start_time": "2026-06-11 15:00"},
                "options": [{"technician_name": "李娜"}],
            },
            "booking": {"status": "idle"},
        }

        result = await main_router_node(state)

        self.assertEqual(result["route_decision"]["action"], "query_availability")
        self.assertEqual(result["route_decision"]["reason"], "refine_availability_context")


if __name__ == "__main__":
    unittest.main()
