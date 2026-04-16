"""
Tests for AgentController.

All agent methods are now async; use AsyncMock throughout.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from agent_controller import AgentController


def make_controller():
    """Create AgentController with all agents mocked."""
    with patch("agent_controller.GuardAgent"), \
         patch("agent_controller.ClassificationAgent"), \
         patch("agent_controller.DetailsAgent"), \
         patch("agent_controller.RecommendationAgent"), \
         patch("agent_controller.OrderTakingAgent"):
        return AgentController()


def make_payload(text: str) -> dict:
    return {"input": {"messages": [{"role": "user", "content": text}]}}


ALLOWED_GUARD = {
    "role": "assistant",
    "content": "",
    "memory": {"agent": "guard_agent", "guard_decision": "allowed"}
}

BLOCKED_GUARD = {
    "role": "assistant",
    "content": "Sorry, I can't help with that.",
    "memory": {"agent": "guard_agent", "guard_decision": "not allowed"}
}


class TestGuardBlocking:
    async def test_blocked_message_returns_guard_response_immediately(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=BLOCKED_GUARD)
        controller.classification_agent.get_response = AsyncMock()

        result = await controller.get_response(make_payload("Write me a poem"))

        assert result["memory"]["guard_decision"] == "not allowed"
        controller.classification_agent.get_response.assert_not_called()

    async def test_blocked_message_does_not_call_any_domain_agent(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=BLOCKED_GUARD)

        for agent_name in ["details_agent", "order_taking_agent", "recommendation_agent"]:
            controller.agent_dict[agent_name] = MagicMock(get_response=AsyncMock())

        await controller.get_response(make_payload("Hack the mainframe"))

        for agent_name in ["details_agent", "order_taking_agent", "recommendation_agent"]:
            controller.agent_dict[agent_name].get_response.assert_not_called()


class TestAgentRouting:
    @pytest.mark.parametrize("agent_name", ["details_agent", "order_taking_agent", "recommendation_agent"])
    async def test_routes_to_correct_agent(self, agent_name):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value={
            "role": "assistant",
            "content": "",
            "memory": {"agent": "classification_agent", "classification_decision": agent_name}
        })

        expected_response = {
            "role": "assistant",
            "content": f"Response from {agent_name}",
            "memory": {"agent": agent_name}
        }
        controller.agent_dict[agent_name] = MagicMock(
            get_response=AsyncMock(return_value=expected_response)
        )

        result = await controller.get_response(make_payload("some user input"))

        controller.agent_dict[agent_name].get_response.assert_called_once()
        assert result["memory"]["agent"] == agent_name

    async def test_classification_is_called_after_guard_allows(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value={
            "role": "assistant",
            "content": "",
            "memory": {"agent": "classification_agent", "classification_decision": "details_agent"}
        })
        controller.agent_dict["details_agent"] = MagicMock(
            get_response=AsyncMock(return_value={"role": "assistant", "content": "info", "memory": {"agent": "details_agent"}})
        )

        await controller.get_response(make_payload("What are your hours?"))

        controller.classification_agent.get_response.assert_called_once()

    async def test_full_pipeline_returns_agent_response(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value={
            "role": "assistant",
            "content": "",
            "memory": {"agent": "classification_agent", "classification_decision": "order_taking_agent"}
        })
        final_response = {
            "role": "assistant",
            "content": "What would you like to order?",
            "memory": {"agent": "order_taking_agent", "step number": "1", "order": []}
        }
        controller.agent_dict["order_taking_agent"] = MagicMock(
            get_response=AsyncMock(return_value=final_response)
        )

        result = await controller.get_response(make_payload("I want to order"))

        assert result == final_response
