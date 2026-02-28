"""JSON-backed state store for lightweight mode."""

import json
import uuid
from pathlib import Path

from ark.models import Session
from ark.state.base import ensure_parent_exists


class JSONStateStore:
    """Persist state in a JSON file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        ensure_parent_exists(file_path)
        if not self.file_path.exists():
            self._write({"sessions": {}})

    def _read(self) -> dict:
        return json.loads(self.file_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict) -> None:
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def create_session(self, platform: str) -> str:
        payload = self._read()
        session_id = str(uuid.uuid4())
        payload["sessions"][session_id] = {"platform": platform}
        self._write(payload)
        return session_id

    def get_session(self, session_id: str) -> Session:
        payload = self._read()
        record = payload["sessions"].get(session_id)
        if record is None:
            raise KeyError(f"Session not found: {session_id}")
        return Session(session_id=session_id, platform=record["platform"])
