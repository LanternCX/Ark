"""Windows adapter implementation."""

from pathlib import Path
from typing import Iterator


class WindowsAdapter:
    """Windows filesystem adapter."""

    def list_roots(self) -> list[Path]:
        roots: list[Path] = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            candidate = Path(f"{letter}:/")
            if candidate.exists():
                roots.append(candidate)
        return roots

    def iter_files(self, root: Path) -> Iterator[Path]:
        for path in root.rglob("*"):
            if path.is_file():
                yield path
