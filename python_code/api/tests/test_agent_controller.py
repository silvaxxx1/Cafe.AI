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


# ── Helpers ───────────────────────────────────────────────────────────────────

async def collect(gen) -> list:
    return [event async for event in gen]


def classify_as(agent_name: str) -> dict:
    return {
        "role": "assistant",
        "content": "",
        "memory": {"agent": "classification_agent", "classification_decision": agent_name}
    }


# ── get_stream_response tests ─────────────────────────────────────────────────

class TestFakeStream:
    async def test_yields_token_events_for_each_word(self):
        response = {"role": "assistant", "content": "Hello world", "memory": {"agent": "test"}}
        events = await collect(AgentController._fake_stream(response))
        token_events = [e for e in events if e["type"] == "token"]
        reassembled = "".join(e["delta"] for e in token_events)
        assert reassembled == "Hello world"

    async def test_last_event_is_done_with_memory(self):
        memory = {"agent": "test", "order": []}
        response = {"role": "assistant", "content": "ok", "memory": memory}
        events = await collect(AgentController._fake_stream(response))
        assert events[-1] == {"type": "done", "memory": memory}

    async def test_empty_content_yields_only_done(self):
        response = {"role": "assistant", "content": "", "memory": {}}
        events = await collect(AgentController._fake_stream(response))
        # single empty-string token + done
        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1


class TestStreamResponseGuard:
    async def test_blocked_message_fake_streams_guard_content(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=BLOCKED_GUARD)

        events = await collect(controller.get_stream_response(make_payload("hack")))

        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) > 0
        reassembled = "".join(e["delta"] for e in token_events)
        assert reassembled == BLOCKED_GUARD["content"]

    async def test_blocked_message_done_has_guard_memory(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=BLOCKED_GUARD)

        events = await collect(controller.get_stream_response(make_payload("hack")))

        done = next(e for e in events if e["type"] == "done")
        assert done["memory"]["guard_decision"] == "not allowed"

    async def test_blocked_message_skips_classification(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=BLOCKED_GUARD)
        controller.classification_agent.get_response = AsyncMock()

        await collect(controller.get_stream_response(make_payload("hack")))

        controller.classification_agent.get_response.assert_not_called()


class TestStreamResponseRouting:
    async def test_delegates_to_agent_get_stream_response_when_present(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value=classify_as("details_agent"))

        async def fake_stream_gen(messages):
            yield {"type": "token", "delta": "RAG "}
            yield {"type": "token", "delta": "answer"}
            yield {"type": "done", "memory": {"agent": "details_agent"}}

        controller.agent_dict["details_agent"] = MagicMock(
            get_stream_response=fake_stream_gen
        )

        events = await collect(controller.get_stream_response(make_payload("tell me about lattes")))

        token_content = "".join(e["delta"] for e in events if e["type"] == "token")
        assert token_content == "RAG answer"
        done = next(e for e in events if e["type"] == "done")
        assert done["memory"]["agent"] == "details_agent"

    async def test_falls_back_to_fake_stream_when_no_get_stream_response(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value=classify_as("order_taking_agent"))

        order_response = {
            "role": "assistant",
            "content": "What would you like?",
            "memory": {"agent": "order_taking_agent", "order": []}
        }
        # MagicMock has no get_stream_response attribute by default
        controller.agent_dict["order_taking_agent"] = MagicMock(
            spec=["get_response"],
            get_response=AsyncMock(return_value=order_response)
        )

        events = await collect(controller.get_stream_response(make_payload("order")))

        token_content = "".join(e["delta"] for e in events if e["type"] == "token")
        assert token_content == order_response["content"]

    async def test_unknown_agent_yields_fallback_message_and_done(self):
        controller = make_controller()
        controller.guard_agent.get_response = AsyncMock(return_value=ALLOWED_GUARD)
        controller.classification_agent.get_response = AsyncMock(return_value=classify_as("nonexistent_agent"))

        events = await collect(controller.get_stream_response(make_payload("something")))

        assert any(e["type"] == "token" for e in events)
        assert any(e["type"] == "done" for e in events)
