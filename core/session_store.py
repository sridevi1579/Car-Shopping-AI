"""
session_store.py — Persistent SQLite-backed session store.

Replaces the in-memory dict used by both agents. Sessions survive
Flask restarts, expire automatically after 24 hours, and are
safe to share across both agents via namespaced keys.

Usage:
    from session_store import sessions

    history = sessions.get("search:abc") or []
    history.append(...)
    sessions.save("search:abc", history)
    sessions.pop("search:abc")
"""

import json
import logging
import os
import sqlite3
import time

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sessions.db")
_TTL     = 24 * 60 * 60  # 24 hours


def _serialize_history(history: list) -> str:
    """Convert history list to JSON, handling Anthropic SDK content blocks."""
    def _serialize_content(content):
        if not isinstance(content, list):
            return content  # plain string — already serializable
        out = []
        for block in content:
            if hasattr(block, "model_dump"):
                out.append(block.model_dump())  # Anthropic SDK object → dict
            elif isinstance(block, dict):
                out.append(block)
            else:
                out.append({"type": "text", "text": str(block)})
        return out

    return json.dumps([
        {"role": m["role"], "content": _serialize_content(m["content"])}
        for m in history
    ])


def _deserialize_history(raw: str) -> list:
    return json.loads(raw)


class SQLiteSessionStore:
    """
    Persistent session store backed by SQLite with TTL expiry.

    Thread-safe: SQLite WAL mode handles concurrent reads/writes.
    """

    def __init__(self, db_path: str = _DB_PATH, ttl: int = _TTL) -> None:
        self._db  = db_path
        self._ttl = ttl
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id         TEXT PRIMARY KEY,
                    history    TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

    # ── public API ────────────────────────────────────────────────────────────

    def get(self, session_id: str) -> list | None:
        """Return history list or None if missing/expired."""
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT history, updated_at FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()

        if not row:
            return None

        history_json, updated_at = row
        if (time.time() - updated_at) > self._ttl:
            self.pop(session_id)
            return None

        return _deserialize_history(history_json)

    def save(self, session_id: str, history: list) -> None:
        """Persist the full history for a session."""
        try:
            payload = _serialize_history(history)
        except Exception:
            logger.exception("Failed to serialize session %s — not saved", session_id)
            return

        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """INSERT INTO sessions (id, history, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       history    = excluded.history,
                       updated_at = excluded.updated_at""",
                (session_id, payload, time.time())
            )

    def pop(self, session_id: str) -> None:
        """Delete a session."""
        with sqlite3.connect(self._db) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


# Module-level singleton — import this in both agents
sessions = SQLiteSessionStore()
