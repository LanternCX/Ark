"""Platform adapter factory helpers."""

import sys

from src.platforms.base import PlatformAdapter
from src.platforms.macos import MacOSAdapter
from src.platforms.windows import WindowsAdapter


def get_platform_adapter(platform_name: str | None = None) -> PlatformAdapter:
    """Return platform adapter based on runtime platform name."""
    normalized = (platform_name or sys.platform).lower()
    if normalized.startswith("win"):
        return WindowsAdapter()
    if normalized == "darwin":
        return MacOSAdapter()
    raise ValueError(f"unsupported platform: {normalized}")
