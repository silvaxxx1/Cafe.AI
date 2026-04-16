"""
Tests for ClassificationAgent.

Covers routing to all 3 valid agents and the malformed-JSON fallback.
"""
import json
import pytest
from unittest.mock import patch, AsyncMock

from agents.classification_agent import ClassificationAgent

VALID_AGENTS = ["details_agent", "order_taking_agent", "recommendation_agent"]


def make_agent():
    with patch("agents.classification_agent.AsyncOpenAI"):
        return ClassificationAgent()


def llm_routes_to(agent_name: str) -> str:
    return json.dumps({
        "chain of thought": "Routing decision",
        "decision": agent_name,
        "message": ""
    })


USER_MSG = [{"role": "user", "content": "I want to order a latte"}]


class TestClassificationRouting:
    @pytest.mark.parametrize("agent_name", VALID_AGENTS)
    async def test_routes_to_each_valid_agent(self, agent_name):
        agent = make_agent()
        with patch("agents.classification_agent.get_chatbot_response", AsyncMock(return_value=llm_routes_to(agent_name))):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["classification_decision"] == agent_name

    async def test_response_shape_has_required_keys(self):
        agent = make_agent()
        with patch("agents.classification_agent.get_chatbot_response", AsyncMock(return_value=llm_routes_to("order_taking_agent"))):
            result = await agent.get_response(USER_MSG)

        assert result["role"] == "assistant"
        assert "content" in result
        assert result["memory"]["agent"] == "classification_agent"
        assert "classification_decision" in result["memory"]


class TestClassificationFallback:
    async def test_invalid_json_falls_back_to_order_taking_agent(self):
        agent = make_agent()
        with patch("agents.classification_agent.get_chatbot_response", AsyncMock(return_value="garbage output")):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["classification_decision"] == "order_taking_agent"

    async def test_missing_decision_key_falls_back_to_order_taking_agent(self):
        agent = make_agent()
        llm_output = json.dumps({"chain of thought": "..."})
        with patch("agents.classification_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["classification_decision"] == "order_taking_agent"

    async def test_empty_string_falls_back(self):
        agent = make_agent()
        with patch("agents.classification_agent.get_chatbot_response", AsyncMock(return_value="")):
            result = await agent.get_response(USER_MSG)

        assert result["memory"]["classification_decision"] == "order_taking_agent"
