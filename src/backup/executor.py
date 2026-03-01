"""Mirror backup copy operations."""

import shutil
from pathlib import Path


def mirror_copy_one(src_root: Path, src_path: Path, dst_root: Path) -> None:
    """Copy one file while preserving source root structure."""
    relative_path = src_path.relative_to(src_root)
    destination = dst_root / src_root.name / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, destination)
