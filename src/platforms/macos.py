"""macOS adapter implementation."""

from pathlib import Path
from typing import Iterator


class MacOSAdapter:
    """macOS filesystem adapter."""

    def __init__(
        self,
        home_dir: Path | None = None,
        volumes_dir: Path | None = None,
    ) -> None:
        self.home_dir = home_dir or Path.home()
        self.volumes_dir = volumes_dir or Path("/Volumes")

    def list_roots(self) -> list[Path]:
        roots: list[Path] = []
        if self.home_dir.exists() and self.home_dir.is_dir():
            roots.append(self.home_dir)
        if self.volumes_dir.exists() and self.volumes_dir.is_dir():
            for candidate in sorted(
                self.volumes_dir.iterdir(), key=lambda item: item.name
            ):
                if candidate.is_dir():
                    roots.append(candidate)
        return roots

    def iter_files(self, root: Path) -> Iterator[Path]:
        for path in sorted(root.rglob("*"), key=lambda item: str(item)):
            if path.is_file():
                yield path
