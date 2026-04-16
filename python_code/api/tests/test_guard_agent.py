"""
Tests for GuardAgent.

Strategy: mock OpenAI at construction time so no real client is created,
then mock get_chatbot_response (AsyncMock) to control LLM output.
Tests cover all code paths in postprocess() and the allowed/blocked decision logic.
"""
import json
import pytest
from unittest.mock import patch, AsyncMock

from agents.guard_agent import GuardAgent


def make_agent():
    with patch("agents.guard_agent.AsyncOpenAI"):
        return GuardAgent()


USER_MSG = [{"role": "user", "content": "What lattes do you have?"}]
OFF_TOPIC_MSG = [{"role": "user", "content": "Write me a poem about the ocean"}]


class TestGuardAgentAllowed:
    async def test_allowed_decision_sets_guard_decision(self):
        agent = make_agent()
        llm_output = json.dumps({
            "chain of thought": "Coffee shop question",
            "decision": "allowed",
            "message": ""
        })
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["guard_decision"] == "allowed"

    async def test_allowed_response_has_empty_content(self):
        agent = make_agent()
        llm_output = json.dumps({"decision": "allowed", "message": ""})
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(USER_MSG)

        assert result["content"] == ""

    async def test_response_shape_has_required_keys(self):
        agent = make_agent()
        llm_output = json.dumps({"decision": "allowed", "message": ""})
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(USER_MSG)

        assert "role" in result
        assert "content" in result
        assert "memory" in result
        assert result["role"] == "assistant"
        assert result["memory"]["agent"] == "guard_agent"


class TestGuardAgentBlocked:
    async def test_blocked_decision_sets_guard_decision(self):
        agent = make_agent()
        llm_output = json.dumps({
            "chain of thought": "Off-topic question",
            "decision": "not allowed",
            "message": "Sorry, I can't help with that. Can I help you with your order?"
        })
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(OFF_TOPIC_MSG)

        assert result["memory"]["guard_decision"] == "not allowed"

    async def test_blocked_response_carries_message(self):
        agent = make_agent()
        block_msg = "Sorry, I can't help with that. Can I help you with your order?"
        llm_output = json.dumps({"decision": "not allowed", "message": block_msg})
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(OFF_TOPIC_MSG)

        assert result["content"] == block_msg


class TestGuardAgentMalformedOutput:
    async def test_invalid_json_defaults_to_allowed(self):
        agent = make_agent()
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value="not json at all")):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["guard_decision"] == "allowed"

    async def test_partial_json_missing_decision_defaults_to_allowed(self):
        agent = make_agent()
        llm_output = json.dumps({"chain of thought": "some thought"})
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["guard_decision"] == "allowed"

    async def test_empty_string_defaults_to_allowed(self):
        agent = make_agent()
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value="")):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["guard_decision"] == "allowed"


class TestGuardAgentMessageTruncation:
    async def test_only_last_3_messages_sent_to_llm(self):
        """Guard should only pass the last 3 messages to the LLM."""
        agent = make_agent()
        messages = [{"role": "user", "content": f"message {i}"} for i in range(6)]
        llm_output = json.dumps({"decision": "allowed", "message": ""})
        mock_llm = AsyncMock(return_value=llm_output)

        with patch("agents.guard_agent.get_chatbot_response", mock_llm):
            await agent.get_response(messages)

        call_args = mock_llm.call_args[0]
        input_messages = call_args[2]
        # system prompt + last 3 user messages
        assert len(input_messages) == 4
        assert input_messages[1]["content"] == "message 3"
        assert input_messages[3]["content"] == "message 5"

    async def test_single_message_does_not_crash(self):
        agent = make_agent()
        llm_output = json.dumps({"decision": "allowed", "message": ""})
        with patch("agents.guard_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response([{"role": "user", "content": "Hi"}])

        assert result["memory"]["guard_decision"] == "allowed"
