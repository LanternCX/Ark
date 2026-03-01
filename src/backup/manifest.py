"""Manifest writing for backup runs."""

from pathlib import Path


def manifest_path(target_root: Path) -> Path:
    """Return manifest location in backup target."""
    return target_root / "ark-manifest.json"
