"""User behavior tools."""

from __future__ import annotations

from langchain_core.tools import tool

from services.user_behavior_service import UserBehaviorService
from .schemas import RecordUserBehaviorInput, tool_result


def _tool_result(*args, **kwargs) -> dict:
    return tool_result(*args, tool_name="record_user_behavior", **kwargs)


@tool(args_schema=RecordUserBehaviorInput)
def record_user_behavior(
    user_id: str = "default_user",
    action_type: str = "",
    action_data: dict | None = None,
    technician_id: str | None = None,
    session_id: str = "default_session",
) -> dict:
    """Record appointment, consultation, or preference-related user behavior."""
    try:
        if not action_type:
            return _tool_result(False, message="缺少行为类型", error="missing_action_type")
        service = UserBehaviorService()
        success = service.record_behavior(
            user_id=user_id,
            action_type=action_type,
            action_data=action_data or {},
            technician_id=technician_id,
            session_id=session_id,
        )
        return _tool_result(success, message="用户行为记录成功" if success else "用户行为记录失败")
    except Exception as e:
        return _tool_result(False, message="用户行为记录失败", error=str(e))
