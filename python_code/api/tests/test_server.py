"""
Tests for the FastAPI HTTP layer (local_server.py).

local_server creates the AgentController at import time, so we patch
AgentController before importing the app to prevent real agent construction.
The chat route is now async; TestClient (via anyio) handles this transparently.
"""
import json
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# Patch AgentController before local_server is imported so agents are never
# constructed for real. This must happen at module level.
def _make_mock_stream(*events):
    """Return an async generator function that yields the given event dicts."""
    async def _gen(payload):
        for event in events:
            yield event
    return _gen


_mock_controller_instance = MagicMock()
_mock_controller_instance.get_response = AsyncMock()
_mock_controller_instance.get_stream_response = _make_mock_stream()

_mock_session_store = MagicMock()
_mock_session_store.get.return_value = []
_mock_session_store.set.return_value = None
_mock_session_store.delete.return_value = None

with patch("agent_controller.AgentController", return_value=_mock_controller_instance), \
     patch("session.SessionStore", return_value=_mock_session_store), \
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


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE response body into a list of data event dicts."""
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            raw = line[6:].strip()
            if raw:
                events.append(json.loads(raw))
    return events


class TestStreamEndpoint:
    _body = {"input": {"messages": [{"role": "user", "content": "Hi"}]}}

    def setup_method(self):
        import asyncio
        from sse_starlette.sse import AppStatus
        # sse-starlette binds the exit-signal Event to the first event loop it runs
        # in. Reset it before each test so the next test's loop can adopt it.
        AppStatus.should_exit_event = asyncio.Event()

    def _stream_events(self, mock_events) -> list[dict]:
        _mock_controller_instance.get_stream_response = _make_mock_stream(*mock_events)
        with client.stream("POST", "/chat/stream", json=self._body) as resp:
            text = resp.read().decode()
        return _parse_sse(text)

    def test_returns_200_with_event_stream_content_type(self):
        _mock_controller_instance.get_stream_response = _make_mock_stream()
        with client.stream("POST", "/chat/stream", json=self._body) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_token_events_forwarded_to_client(self):
        events = self._stream_events([
            {"type": "token", "delta": "Hello "},
            {"type": "token", "delta": "there"},
            {"type": "done", "memory": {"agent": "test"}},
        ])
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) == 2
        assert "".join(e["delta"] for e in token_events) == "Hello there"

    def test_done_event_includes_memory(self):
        memory = {"agent": "recommendation_agent"}
        events = self._stream_events([
            {"type": "token", "delta": "ok"},
            {"type": "done", "memory": memory},
        ])
        done = next(e for e in events if e["type"] == "done")
        assert done["memory"] == memory

    def test_missing_input_returns_422(self):
        resp = client.post("/chat/stream", json={"messages": [{"role": "user", "content": "Hi"}]})
        assert resp.status_code == 422

    def test_empty_messages_returns_422(self):
        resp = client.post("/chat/stream", json={"input": {"messages": []}})
        assert resp.status_code == 422

    def test_stream_controller_receives_correct_messages(self):
        received = []

        async def capturing_gen(payload):
            received.append(payload)
            yield {"type": "done", "memory": {}}

        _mock_controller_instance.get_stream_response = capturing_gen
        with client.stream("POST", "/chat/stream", json=self._body) as resp:
            resp.read()

        assert received[0]["input"]["messages"] == self._body["input"]["messages"]

    def test_session_saved_after_stream_completes(self):
        _mock_session_store.set.reset_mock()
        events = [
            {"type": "token", "delta": "Hello "},
            {"type": "token", "delta": "there"},
            {"type": "done", "memory": {"agent": "test_agent"}},
        ]
        self._stream_events(events)
        _mock_session_store.set.assert_called_once()
        saved_messages = _mock_session_store.set.call_args[0][1]
        assistant_msg = saved_messages[-1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["content"] == "Hello there"
        assert assistant_msg["memory"]["agent"] == "test_agent"


class TestSessionEndpoint:
    _messages = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]

    def test_get_session_returns_empty_list_for_unknown_id(self):
        _mock_session_store.get.return_value = []
        resp = client.get("/session/unknown-id")
        assert resp.status_code == 200
        assert resp.json() == {"messages": []}

    def test_get_session_returns_stored_messages(self):
        _mock_session_store.get.return_value = self._messages
        resp = client.get("/session/abc123")
        assert resp.status_code == 200
        assert resp.json()["messages"] == self._messages

    def test_get_session_calls_store_with_correct_id(self):
        _mock_session_store.get.return_value = []
        client.get("/session/my-session-id")
        _mock_session_store.get.assert_called_with("my-session-id")

    def test_delete_session_returns_200(self):
        resp = client.delete("/session/abc123")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"

    def test_delete_session_calls_store_delete(self):
        _mock_session_store.delete.reset_mock()
        client.delete("/session/to-delete")
        _mock_session_store.delete.assert_called_once_with("to-delete")

    def test_chat_saves_session_after_response(self):
        _mock_session_store.set.reset_mock()
        mock_response = {"role": "assistant", "content": "Hi!", "memory": {"agent": "guard_agent"}}
        _mock_controller_instance.get_response = AsyncMock(return_value=mock_response)

        client.post("/chat", json={"input": {"messages": [{"role": "user", "content": "Hi"}]}, "session_id": "s1"})

        _mock_session_store.set.assert_called_once()
        call_args = _mock_session_store.set.call_args[0]
        assert call_args[0] == "s1"
        assert call_args[1][-1] == mock_response
