import json
import sqlite3
import time


class SessionStore:
    def __init__(self, path: str = "sessions.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions "
            "(id TEXT PRIMARY KEY, messages TEXT, ts REAL)"
        )
        self.conn.commit()

    def get(self, session_id: str) -> list:
        row = self.conn.execute(
            "SELECT messages FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return json.loads(row[0]) if row else []

    def set(self, session_id: str, messages: list) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
            (session_id, json.dumps(messages), time.time()),
        )
        self.conn.commit()

    def delete(self, session_id: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
