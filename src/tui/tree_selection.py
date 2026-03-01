"""Tree selection state for stage 3 interactive review."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath


class SelectionState(str, Enum):
    """Selection state for a tree node."""

    UNCHECKED = "unchecked"
    PARTIAL = "partial"
    CHECKED = "checked"


@dataclass
class TreeSelectionState:
    """In-memory tree and selected file set."""

    children_by_path: dict[str, set[str]] = field(default_factory=dict)
    parent_by_path: dict[str, str] = field(default_factory=dict)
    files: set[str] = field(default_factory=set)
    directories: set[str] = field(default_factory=set)
    selected_files: set[str] = field(default_factory=set)

    @classmethod
    def from_paths(
        cls,
        paths: list[str],
        selected_files: set[str] | None = None,
    ) -> TreeSelectionState:
        state = cls()
        selected = {normalize_path(path) for path in (selected_files or set())}

        for raw_path in paths:
            path = normalize_path(raw_path)
            parts = _path_prefixes(path)
            if not parts:
                continue

            state.files.add(parts[-1])
            state.selected_files.update({parts[-1]} & selected)

            for idx, node in enumerate(parts):
                parent = "" if idx == 0 else parts[idx - 1]
                state.parent_by_path[node] = parent
                state.children_by_path.setdefault(parent, set()).add(node)
                state.children_by_path.setdefault(node, set())
                if idx < len(parts) - 1:
                    state.directories.add(node)

        return state

    def is_dir(self, node_path: str) -> bool:
        """Return whether node is a directory."""
        return normalize_path(node_path) in self.directories

    def children(self, node_path: str) -> list[str]:
        """Return sorted children of one directory path."""
        path = normalize_path(node_path)
        items = list(self.children_by_path.get(path, set()))
        return sorted(
            items, key=lambda item: (0 if item in self.directories else 1, item)
        )

    def selection_state(self, node_path: str) -> SelectionState:
        """Return tri-state for node."""
        path = normalize_path(node_path)
        if path not in self.directories:
            return (
                SelectionState.CHECKED
                if path in self.selected_files
                else SelectionState.UNCHECKED
            )

        descendants = self._descendant_files(path)
        if not descendants:
            return SelectionState.UNCHECKED
        selected_count = len(descendants & self.selected_files)
        if selected_count == 0:
            return SelectionState.UNCHECKED
        if selected_count == len(descendants):
            return SelectionState.CHECKED
        return SelectionState.PARTIAL

    def toggle(self, node_path: str) -> None:
        """Toggle one file or one directory recursively."""
        path = normalize_path(node_path)
        if path in self.directories:
            descendants = self._descendant_files(path)
            if not descendants:
                return
            if self.selection_state(path) == SelectionState.CHECKED:
                self.selected_files.difference_update(descendants)
            else:
                self.selected_files.update(descendants)
            return

        if path in self.selected_files:
            self.selected_files.remove(path)
        else:
            self.selected_files.add(path)

    def _descendant_files(self, node_path: str) -> set[str]:
        descendants: set[str] = set()
        stack = list(self.children_by_path.get(node_path, set()))
        while stack:
            item = stack.pop()
            if item in self.directories:
                stack.extend(self.children_by_path.get(item, set()))
            elif item in self.files:
                descendants.add(item)
        return descendants

    def descendant_files(self, node_path: str) -> set[str]:
        """Return all descendant file paths for a directory node."""
        return self._descendant_files(normalize_path(node_path))


def paginate_items(
    items: list[str], page_size: int, page_index: int
) -> tuple[list[str], int]:
    """Return one page and total page count."""
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    if not items:
        return [], 1

    total_pages = (len(items) + page_size - 1) // page_size
    clamped_index = max(0, min(page_index, total_pages - 1))
    start = clamped_index * page_size
    end = start + page_size
    return items[start:end], total_pages


def normalize_path(path: str) -> str:
    """Normalize path string to slash-separated canonical form."""
    raw = path.replace("\\", "/").strip()
    if not raw:
        return raw
    value = str(PurePosixPath(raw))
    if value != "/":
        return value.rstrip("/")
    return value


def _path_prefixes(path: str) -> list[str]:
    pure = PurePosixPath(path)
    parts = pure.parts
    if not parts:
        return []

    prefixes: list[str] = []
    current = ""
    for part in parts:
        if part == "/":
            continue
        if not current:
            current = f"/{part}" if path.startswith("/") else part
        else:
            current = f"{current}/{part}"
        prefixes.append(current)
    return prefixes
