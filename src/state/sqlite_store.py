"""SQLite-backed state store."""

import sqlite3
import uuid
from pathlib import Path

from src.models import Session
from src.state.base import ensure_parent_exists


class SQLiteStateStore:
    """Persist state with local SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        ensure_parent_exists(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, platform TEXT NOT NULL)"
            )

    def create_session(self, platform: str) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, platform) VALUES (?, ?)",
                (session_id, platform),
            )
        return session_id

    def get_session(self, session_id: str) -> Session:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, platform FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Session not found: {session_id}")
        return Session(session_id=row[0], platform=row[1])
