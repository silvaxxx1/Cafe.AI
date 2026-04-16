"""
Tests for the FastAPI HTTP layer (local_server.py).

local_server creates the AgentController at import time, so we patch
AgentController before importing the app to prevent real agent construction.
The chat route is now async; TestClient (via anyio) handles this transparently.
"""
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# Patch AgentController before local_server is imported so agents are never
# constructed for real. This must happen at module level.
_mock_controller_instance = MagicMock()
_mock_controller_instance.get_response = AsyncMock()

with patch("agent_controller.AgentController", return_value=_mock_controller_instance), \
     patch("agents.guard_agent.AsyncOpenAI"), \
     patch("agents.classification_agent.AsyncOpenAI"), \
     patch("agents.order_taking_agent.AsyncOpenAI"), \
     patch("agents.recommendation_agent.AsyncOpenAI"), \
     patch("agents.details_agent.AsyncOpenAI"):
    for mod in list(sys.modules.keys()):
        if mod in ("local_server",):
            del sys.modules[mod]
    from local_server import app

from fastapi.testclient import TestClient

client = TestClient(app)


class TestHealthEndpoint:
    def test_get_root_returns_200(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_get_root_contains_status_ok(self):
        resp = client.get("/")
        assert resp.json()["status"] == "ok"


class TestChatEndpoint:
    def _post_chat(self, messages: list):
        return client.post("/chat", json={"input": {"messages": messages}})

    def test_happy_path_returns_200(self):
        mock_response = {
            "role": "assistant",
            "content": "Hello! How can I help?",
            "memory": {"agent": "guard_agent", "guard_decision": "allowed"}
        }
        _mock_controller_instance.get_response = AsyncMock(return_value=mock_response)

        resp = self._post_chat([{"role": "user", "content": "Hi"}])

        assert resp.status_code == 200

    def test_happy_path_output_wrapped_correctly(self):
        mock_response = {
            "role": "assistant",
            "content": "Hello!",
            "memory": {"agent": "guard_agent", "guard_decision": "allowed"}
        }
        _mock_controller_instance.get_response = AsyncMock(return_value=mock_response)

        resp = self._post_chat([{"role": "user", "content": "Hi"}])

        body = resp.json()
        assert "output" in body
        assert body["output"]["role"] == "assistant"
        assert body["output"]["content"] == "Hello!"

    def test_controller_receives_messages(self):
        _mock_controller_instance.get_response = AsyncMock(return_value={
            "role": "assistant", "content": "ok", "memory": {}
        })
        messages = [{"role": "user", "content": "I want a latte"}]
        self._post_chat(messages)

        call_args = _mock_controller_instance.get_response.call_args[0][0]
        assert call_args["input"]["messages"] == messages

    def test_missing_input_field_returns_422(self):
        resp = client.post("/chat", json={"messages": [{"role": "user", "content": "Hi"}]})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        resp = client.post("/chat", json={})
        assert resp.status_code == 422

    def test_controller_exception_returns_500(self):
        _mock_controller_instance.get_response = AsyncMock(side_effect=RuntimeError("Something exploded"))

        resp = self._post_chat([{"role": "user", "content": "Hi"}])

        assert resp.status_code == 500
        # Reset for subsequent tests
        _mock_controller_instance.get_response = AsyncMock()

    def test_blocked_message_still_returns_200(self):
        """A 'not allowed' guard response is a valid response, not an HTTP error."""
        blocked_response = {
            "role": "assistant",
            "content": "Sorry, I can't help with that.",
            "memory": {"agent": "guard_agent", "guard_decision": "not allowed"}
        }
        _mock_controller_instance.get_response = AsyncMock(return_value=blocked_response)

        resp = self._post_chat([{"role": "user", "content": "hack the planet"}])

        assert resp.status_code == 200
        assert resp.json()["output"]["memory"]["guard_decision"] == "not allowed"
