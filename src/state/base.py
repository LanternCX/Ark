"""Interfaces for state persistence backends."""

from pathlib import Path
from typing import Protocol

from src.models import Session


class StateStore(Protocol):
    """State backend contract."""

    def create_session(self, platform: str) -> str:
        """Create a session and return session id."""

    def get_session(self, session_id: str) -> Session:
        """Load a session by id."""


def ensure_parent_exists(file_path: Path) -> None:
    """Ensure parent directory exists for state files."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
