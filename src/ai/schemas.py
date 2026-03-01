"""Structured data contracts for AI requests and responses."""

from pydantic import BaseModel, Field


class MetadataRecord(BaseModel):
    """Minimal metadata sent to AI for classification."""

    basename: str
    extension: str | None = None
    parent_dir_name: str
    size_bucket: str
    mtime_bucket: str


class ClassificationResult(BaseModel):
    """Single AI classification result."""

    label: str = Field(description="keep or drop")
    tier_hint: str = Field(description="tier1, tier2, or tier3")
    reason: str
    confidence: float
    needs_review: bool
