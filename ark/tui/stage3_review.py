"""Stage 3 final review helpers."""

from dataclasses import dataclass
from typing import Callable

import questionary
from rich.console import Console
from rich.table import Table

from ark.tui.tree_selection import SelectionState, TreeSelectionState, paginate_items


@dataclass(frozen=True)
class PathReviewRow:
    """Single path candidate shown in final backup review."""

    path: str
    tier: str
    size_bytes: int
    reason: str
    confidence: float
    ai_risk: str = "neutral"


def default_selected_tiers() -> tuple[str, str]:
    """Return default tier inclusion strategy."""
    return ("tier1", "tier2_optional")


def render_stage3_table(
    rows: list[PathReviewRow], console: Console | None = None
) -> None:
    """Render the final review table for Tier 1 and Tier 2 rows."""
    ui = console or Console()
    table = Table(title="Stage 3 - Final Review")
    table.add_column("Tier")
    table.add_column("Path")
    table.add_column("Size")
    table.add_column("Confidence", justify="right")
    table.add_column("Reason")
    for row in rows:
        table.add_row(
            row.tier,
            row.path,
            _human_bytes(row.size_bytes),
            f"{row.confidence:.2f}",
            row.reason,
        )
    ui.print(table)


def run_stage3_review(
    rows: list[PathReviewRow],
    checkbox_prompt: Callable[[str, list[dict], list[str]], list[str]] | None = None,
    action_prompt: Callable[[str, list[dict]], str] | None = None,
    confirm_prompt: Callable[[str, bool], bool] | None = None,
    console: Console | None = None,
    page_size: int = 20,
    hide_low_value_default: bool = True,
) -> set[str]:
    """Run final TUI review for backup path selection."""
    filtered_rows = [row for row in rows if row.tier in {"tier1", "tier2"}]
    render_stage3_table(filtered_rows, console=console)

    if checkbox_prompt and action_prompt is None:
        selected = _run_checkbox_mode(filtered_rows, checkbox_prompt)
    else:
        action_fn = action_prompt or _default_action_prompt
        selected = _run_tree_mode(
            filtered_rows,
            action_fn,
            page_size=page_size,
            hide_low_value_default=hide_low_value_default,
        )

    confirm_fn = confirm_prompt or _default_confirm_prompt
    approved = confirm_fn("Proceed with backup execution?", True)
    if not approved:
        return set()
    return selected


def _run_checkbox_mode(
    filtered_rows: list[PathReviewRow],
    checkbox_fn: Callable[[str, list[dict], list[str]], list[str]],
) -> set[str]:
    """Run legacy flat checkbox mode."""

    choices = [
        {
            "name": (
                f"[{row.tier}] {row.path} | size={_human_bytes(row.size_bytes)} | "
                f"conf={row.confidence:.2f} | {row.reason}"
            ),
            "value": row.path,
        }
        for row in filtered_rows
    ]
    defaults = [row.path for row in filtered_rows if row.tier == "tier1"]

    selected = checkbox_fn("Final backup selection", choices, defaults)
    return set(selected)


def _run_tree_mode(
    filtered_rows: list[PathReviewRow],
    action_prompt: Callable[[str, list[dict]], str],
    page_size: int,
    hide_low_value_default: bool,
) -> set[str]:
    """Run tree-based paginated decision flow."""
    defaults = {row.path for row in filtered_rows if row.tier == "tier1"}
    low_value_files = {row.path for row in filtered_rows if row.ai_risk == "low_value"}
    candidates = [row.path for row in filtered_rows]
    state = TreeSelectionState.from_paths(candidates, selected_files=defaults)

    current_dir = ""
    page_index = 0
    show_low_value = not hide_low_value_default

    while True:
        nodes = state.children(current_dir)
        visible_nodes = [
            node
            for node in nodes
            if _is_visible_node(
                node=node,
                state=state,
                low_value_files=low_value_files,
                show_low_value=show_low_value,
            )
        ]
        page_items, total_pages = paginate_items(visible_nodes, page_size, page_index)
        page_index = max(0, min(page_index, total_pages - 1))

        choices: list[dict] = []
        if current_dir:
            choices.append({"name": ".. Up one level", "value": "up"})
        if page_index > 0:
            choices.append({"name": "Previous page", "value": "prev"})
        if page_index < total_pages - 1:
            choices.append({"name": "Next page", "value": "next"})

        for node in page_items:
            marker = _marker_for(state.selection_state(node))
            name = _display_name(node)
            if state.is_dir(node):
                choices.append(
                    {
                        "name": f"{marker} Toggle folder: {name}/",
                        "value": f"toggle::{node}",
                    }
                )
                choices.append(
                    {
                        "name": f"Open folder: {name}/",
                        "value": f"enter::{node}",
                    }
                )
            else:
                choices.append(
                    {
                        "name": f"{marker} Toggle file: {name}",
                        "value": f"toggle::{node}",
                    }
                )

        choices.append(
            {
                "name": (
                    "Show low-value branches"
                    if not show_low_value
                    else "Hide low-value branches"
                ),
                "value": "toggle_low_value",
            }
        )
        choices.append({"name": "Done", "value": "done"})

        hidden_count = _hidden_node_count(nodes, visible_nodes)
        message = (
            f"Stage 3 Tree Review | dir={current_dir or '/'} | "
            f"page={page_index + 1}/{total_pages} | hidden={hidden_count}"
        )
        action = action_prompt(message, choices)

        if action == "done":
            break
        if action == "up":
            current_dir = state.parent_by_path.get(current_dir, "")
            page_index = 0
            continue
        if action == "next":
            page_index += 1
            continue
        if action == "prev":
            page_index -= 1
            continue
        if action == "toggle_low_value":
            show_low_value = not show_low_value
            page_index = 0
            continue
        if action.startswith("toggle::"):
            state.toggle(action.split("::", 1)[1])
            continue
        if action.startswith("enter::"):
            current_dir = action.split("::", 1)[1]
            page_index = 0
            continue

    return state.selected_files & set(candidates)


def _default_checkbox_prompt(
    message: str, choices: list[dict], default: list[str]
) -> list[str]:
    """Default checkbox implementation."""
    default_set = set(default)
    prompt_choices = []
    for choice in choices:
        item = dict(choice)
        item["checked"] = bool(item.get("value") in default_set)
        prompt_choices.append(item)

    result = questionary.checkbox(
        message=message,
        choices=prompt_choices,
    ).ask()
    return result or []


def _default_action_prompt(message: str, choices: list[dict]) -> str:
    """Default tree action prompt using questionary select."""
    result = questionary.select(message=message, choices=choices).ask()
    return result or "done"


def _default_confirm_prompt(message: str, default: bool) -> bool:
    """Default confirmation implementation."""
    result = questionary.confirm(message=message, default=default).ask()
    return bool(result)


def _human_bytes(size_bytes: int) -> str:
    """Format bytes into a compact human readable string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.1f} {units[idx]}"


def _marker_for(state: SelectionState) -> str:
    if state == SelectionState.CHECKED:
        return "[x]"
    if state == SelectionState.PARTIAL:
        return "[-]"
    return "[ ]"


def _display_name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _is_visible_node(
    node: str,
    state: TreeSelectionState,
    low_value_files: set[str],
    show_low_value: bool,
) -> bool:
    if show_low_value:
        return True
    if state.is_dir(node):
        descendants = state.descendant_files(node)
        if not descendants:
            return True
        return bool(descendants - low_value_files)
    return node not in low_value_files


def _hidden_node_count(all_nodes: list[str], visible_nodes: list[str]) -> int:
    return max(0, len(all_nodes) - len(visible_nodes))
