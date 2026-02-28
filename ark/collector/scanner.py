"""Filesystem scanning helpers."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SuffixSummary:
    """Deduplicated extension and no-extension name summary."""

    extensions: set[str]
    no_extension_names: set[str]


def collect_suffix_summary(roots: list[Path]) -> SuffixSummary:
    """Collect deduplicated suffix summary from file roots."""
    extensions: set[str] = set()
    no_extension_names: set[str] = set()

    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix:
                extensions.add(path.suffix.lower())
            else:
                no_extension_names.add(path.name)

    return SuffixSummary(extensions=extensions, no_extension_names=no_extension_names)
