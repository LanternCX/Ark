"""Domain models for Ark."""

from pydantic import BaseModel


class Session(BaseModel):
    """A backup scan session."""

    session_id: str
    platform: str
