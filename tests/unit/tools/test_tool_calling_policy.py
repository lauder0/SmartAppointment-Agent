from agents._shared.tool_calling.policy import (
    get_allowed_tool_names,
    get_allowed_tools,
    is_tool_allowed,
)


def test_consultation_allows_only_read_tools():
    names = get_allowed_tool_names("consultation", "answer_knowledge")

    assert "search_knowledge" in names
    assert "recommend_service_item" in names
    assert "create_appointment" not in names
    assert is_tool_allowed("search_knowledge", "consultation", "answer_knowledge")
    assert not is_tool_allowed("create_appointment", "consultation", "answer_knowledge")


def test_recommendation_can_query_and_rank_without_write_tools():
    names = get_allowed_tool_names("recommendation", "generate_recommendation")

    assert "query_availability" in names
    assert "rank_technicians" in names
    assert "recall_preferences" in names
    assert "create_appointment" not in names
    assert is_tool_allowed("rank_technicians", "recommendation", "generate_recommendation")
    assert not is_tool_allowed("record_user_behavior", "recommendation", "generate_recommendation")


def test_policy_returns_langchain_tools_for_allowed_names():
    tools = get_allowed_tools("availability", "query_availability")
    tool_names = {tool.name for tool in tools}

    assert {"query_availability", "get_all_technicians"}.issubset(tool_names)
    assert "create_appointment" not in tool_names
