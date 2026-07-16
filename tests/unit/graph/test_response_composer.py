from __future__ import annotations

import pytest

from agents.response_writer.composer import ResponseComposer


def test_booking_confirmation_keeps_required_fields():
    response = ResponseComposer().compose(
        "booking_confirmation",
        {
            "time_line": "2026年6月1日 10:00-11:00",
            "service_type": "全身推拿",
            "duration_minutes": 60,
            "technician_name": "李娜",
        },
    )

    assert response.policy == "template_required"
    assert response.agent_label == "预约机器人"
    assert response.reply.startswith("[REPLY][预约机器人]")
    assert "时间：2026年6月1日 10:00-11:00" in response.reply
    assert "项目：全身推拿" in response.reply
    assert "时长：60分钟" in response.reply
    assert "技师：李娜" in response.reply
    assert "请问是否确认预约" in response.reply


def test_booking_success_keeps_completion_facts():
    response = ResponseComposer().reply(
        "booking_success",
        {
            "technician_name": "李娜",
            "start_time": "2026-06-11 10:00",
            "end_time_text": "11:00",
            "service_type": "全身推拿",
            "duration_minutes": 60,
        },
    )

    assert response.startswith("[REPLY][预约机器人]")
    assert "预约成功" in response
    assert "李娜" in response
    assert "2026-06-11 10:00-11:00" in response
    assert "全身推拿" in response


def test_pending_greeting_uses_booking_agent_label():
    response = ResponseComposer().reply(
        "greeting",
        {"agent_label": "预约机器人", "booking_pending": True},
    )

    assert response.startswith("[REPLY][预约机器人]")
    assert "等待您确认" in response


@pytest.mark.asyncio
async def test_low_risk_availability_result_uses_llm_when_facts_are_preserved(monkeypatch):
    class FakeMessage:
        content = "明天下午 15:00 可以约李娜，您可以继续告诉我项目或直接确认想约哪位技师。"

    class FakeModel:
        async def ainvoke(self, prompt):
            return FakeMessage()

    monkeypatch.setattr(
        "agents.response_writer.composer.create_chat_model",
        lambda temperature=0.2: FakeModel(),
    )

    response = await ResponseComposer(enable_llm=True).areply(
        "availability_result",
        {
            "body": "模板：2026-06-11 15:00 可约技师：李娜、赵敏。",
            "criteria": {"start_time": "2026-06-11 15:00"},
            "available_technician_names": ["李娜", "赵敏"],
        },
    )

    assert response.startswith("[REPLY][咨询机器人]")
    assert "明天下午 15:00 可以约李娜" in response
    assert "模板：" not in response


@pytest.mark.asyncio
async def test_low_risk_availability_result_falls_back_when_llm_drops_facts(monkeypatch):
    class FakeMessage:
        content = "这个时间看起来有人可以安排，您可以继续预约。"

    class FakeModel:
        async def ainvoke(self, prompt):
            return FakeMessage()

    monkeypatch.setattr(
        "agents.response_writer.composer.create_chat_model",
        lambda temperature=0.2: FakeModel(),
    )

    response = await ResponseComposer(enable_llm=True).areply(
        "availability_result",
        {
            "body": "模板：2026-06-11 15:00 可约技师：李娜、赵敏。",
            "criteria": {"start_time": "2026-06-11 15:00"},
            "available_technician_names": ["李娜", "赵敏"],
        },
    )

    assert "模板：2026-06-11 15:00 可约技师：李娜、赵敏。" in response
