from __future__ import annotations

import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from api.chat_handler import _extract_user_id
from api.appointment import _build_appointment_message, create_appointment
from api.consultation import ask_consultation
from api.task import classify_task
from api.core.response_models import AppointmentRequest, ConsultationRequest, TaskClassificationRequest
from agents.specialists.booking.actions import booking_guard_node
from config.time_config import time_config


GRAPH_RESULT = {
    "session_id": "s1",
    "final_response": "[REPLY]ok",
    "route_decision": {"action": "start_or_continue_booking"},
    "booking": {"draft": {"service_type": "shoulder massage"}},
    "tool_results": {},
}


class LangGraphApiTests(unittest.IsolatedAsyncioTestCase):
    def test_appointment_message_contains_structured_fields(self):
        request = AppointmentRequest(
            user_id="u1",
            service_type="shoulder massage",
            preferred_time="2026-06-08 19:00",
            duration_minutes=60,
            gender_preference="female",
            technician_name="Alice",
            preference="strong pressure",
        )

        message = _build_appointment_message(request)

        self.assertIn("shoulder massage", message)
        self.assertIn("2026-06-08 19:00", message)
        self.assertIn("60 minutes", message)
        self.assertIn("Alice", message)

    async def test_appointment_api_uses_langgraph(self):
        request = AppointmentRequest(
            user_id="u1",
            service_type="shoulder massage",
            preferred_time="2026-06-08 19:00",
        )
        with patch("api.appointment.process_user_input_graph", new=AsyncMock(return_value=GRAPH_RESULT)) as mocked:
            response = await create_appointment(request)

        mocked.assert_awaited_once()
        self.assertEqual(response.data["reply"], "[REPLY]ok")
        self.assertEqual(response.data["agent"], "appointment")

    async def test_consultation_api_uses_langgraph(self):
        request = ConsultationRequest(user_id="u1", question="What services do you offer?")
        with patch("api.consultation.process_user_input_graph", new=AsyncMock(return_value=GRAPH_RESULT)) as mocked:
            response = await ask_consultation(request)

        mocked.assert_awaited_once()
        self.assertEqual(response.data["answer"], "[REPLY]ok")

    async def test_task_api_uses_langgraph(self):
        request = TaskClassificationRequest(text="I want to book tomorrow", context={"user_id": "u1"})
        with patch("api.task.process_user_input_graph", new=AsyncMock(return_value=GRAPH_RESULT)) as mocked:
            response = await classify_task(request)

        mocked.assert_awaited_once()
        self.assertEqual(response.data["intent"], "appointment")

    def test_chat_wrapper_extracts_user_id_from_context(self):
        self.assertEqual(_extract_user_id(context={"user_id": "u1"}), "u1")
        self.assertEqual(_extract_user_id(state={"user_id": "u2"}), "u2")
        self.assertEqual(_extract_user_id(), "default_user")

    async def test_booking_guard_blocks_unconfirmed_booking(self):
        state = {
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {
                    "service_type": "背部推拿",
                    "start_time": "2026-06-10 15:00",
                    "duration_minutes": 40,
                    "technician_id": 1,
                },
            },
            "tool_results": {},
        }

        result = await booking_guard_node(state)

        self.assertEqual(result["booking"]["status"], "drafting")
        self.assertFalse(result["tool_results"]["booking_guard"]["success"])
        self.assertIn("不能直接创建", result["final_response"])

    async def test_booking_guard_allows_confirmed_available_booking(self):
        start_time = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))
        state = {
            "focus_context": {},
            "booking": {
                "status": "confirmed",
                "draft": {
                    "service_type": "背部推拿",
                    "start_time": start_time,
                    "duration_minutes": 40,
                    "technician_id": 1,
                },
                "selected_option": {"technician_id": 1, "technician_name": "张伟"},
            },
            "tool_results": {},
        }

        with patch("agents.specialists.booking.actions.AppointmentService") as service_cls:
            service_cls.return_value.is_technician_available.return_value = True
            result = await booking_guard_node(state)

        self.assertTrue(result["tool_results"]["booking_guard"]["success"])
        self.assertEqual(result["booking"]["status"], "confirmed")
        self.assertEqual(result["booking"]["guard_result"]["reason"], "ready_to_create")


if __name__ == "__main__":
    unittest.main()
