import pytest
from session import SessionStore


@pytest.fixture
def store(tmp_path):
    return SessionStore(path=str(tmp_path / "test.db"))


class TestSessionStoreGet:
    def test_returns_empty_list_for_unknown_session(self, store):
        assert store.get("nonexistent") == []

    def test_returns_empty_list_after_init(self, store):
        assert store.get("abc") == []


class TestSessionStoreSet:
    def test_roundtrip(self, store):
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        store.set("s1", messages)
        assert store.get("s1") == messages

    def test_overwrite_replaces_previous(self, store):
        store.set("s1", [{"role": "user", "content": "first"}])
        store.set("s1", [{"role": "user", "content": "second"}])
        assert store.get("s1")[0]["content"] == "second"

    def test_multiple_sessions_are_independent(self, store):
        store.set("a", [{"role": "user", "content": "session A"}])
        store.set("b", [{"role": "user", "content": "session B"}])
        assert store.get("a")[0]["content"] == "session A"
        assert store.get("b")[0]["content"] == "session B"

    def test_preserves_memory_field(self, store):
        messages = [{"role": "assistant", "content": "ok", "memory": {"agent": "order_taking_agent", "order": []}}]
        store.set("s1", messages)
        restored = store.get("s1")
        assert restored[0]["memory"]["agent"] == "order_taking_agent"


class TestSessionStoreDelete:
    def test_delete_removes_session(self, store):
        store.set("s1", [{"role": "user", "content": "hi"}])
        store.delete("s1")
        assert store.get("s1") == []

    def test_delete_nonexistent_is_safe(self, store):
        store.delete("does-not-exist")  # should not raise
