"""Cross-platform adapter contracts."""

from pathlib import Path
from typing import Iterator, Protocol


class PlatformAdapter(Protocol):
    """Platform adapter contract for scanning and filtering."""

    def list_roots(self) -> list[Path]:
        """List scan roots for the platform."""

    def iter_files(self, root: Path) -> Iterator[Path]:
        """Iterate files under a root."""
