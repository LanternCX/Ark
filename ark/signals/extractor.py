"""Extract lightweight local signals for tiering."""

from pathlib import Path


def extension_score(path: Path) -> float:
    """Return a baseline score from extension presence."""
    if path.suffix:
        return 0.6
    return 0.3
