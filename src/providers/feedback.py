"""Feedback provider for user override reuse."""

from pathlib import Path


def feedback_file_path(base_dir: Path) -> Path:
    """Return the feedback storage file path."""
    return base_dir / "feedback.json"
