from agents.specialists.booking_agent.message_builder import MessageBuilder


def test_missing_information_prompt_does_not_expose_internal_field_names():
    message = MessageBuilder().create_missing_info_questions(["technician_id", "internal_token"])

    assert "technician_id" not in message
    assert "internal_token" not in message
    assert "重新选择一位可约技师" in message
