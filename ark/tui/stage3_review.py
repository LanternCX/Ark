"""Stage 3 final review helpers."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

import questionary
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import RadioList
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ark.tui.tree_selection import SelectionState, TreeSelectionState, paginate_items

_TREE_ACTION_HINT = (
    "Enter=select(open/toggle/control), Right=open, Space=toggle, "
    "Left/b/h=up, n/p=page, a/f=filter, q/esc=done"
)


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
    resume_state: dict | None = None,
    checkpoint_callback: Callable[[dict], None] | None = None,
    ai_directory_decision_fn: (
        Callable[[str, list[str], list[str]], dict[str, object]] | None
    ) = None,
) -> set[str]:
    """Run final TUI review for backup path selection."""
    filtered_rows = [row for row in rows if row.tier in {"tier1", "tier2"}]
    ui = console or Console()
    _render_stage3_banner(ui, filtered_rows)

    if checkbox_prompt and action_prompt is None:
        selected = _run_checkbox_mode(filtered_rows, checkbox_prompt)
    else:
        action_fn = action_prompt or _default_action_prompt
        selected = _run_tree_mode(
            filtered_rows,
            action_fn,
            page_size=page_size,
            hide_low_value_default=hide_low_value_default,
            resume_state=resume_state,
            checkpoint_callback=checkpoint_callback,
            console=ui,
            ai_directory_decision_fn=ai_directory_decision_fn,
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
    resume_state: dict | None,
    checkpoint_callback: Callable[[dict], None] | None,
    console: Console,
    ai_directory_decision_fn: Callable[[str, list[str], list[str]], dict[str, object]]
    | None,
) -> set[str]:
    """Run tree-based paginated decision flow."""
    defaults = {row.path for row in filtered_rows if row.tier == "tier1"}
    if resume_state and resume_state.get("selected_paths"):
        defaults = {str(path) for path in resume_state.get("selected_paths", [])}
    low_value_files = {row.path for row in filtered_rows if row.ai_risk == "low_value"}
    candidates = [row.path for row in filtered_rows]

    if ai_directory_decision_fn and not (
        resume_state and resume_state.get("selected_paths")
    ):
        defaults, ai_decisions = _apply_ai_directory_decisions(
            candidates,
            defaults,
            ai_directory_decision_fn,
        )
        _render_ai_dfs_summary(console, ai_decisions)

    state = TreeSelectionState.from_paths(candidates, selected_files=defaults)

    current_dir = str(resume_state.get("current_dir", "")) if resume_state else ""
    page_index = int(resume_state.get("page_index", 0)) if resume_state else 0
    show_low_value = (
        bool(resume_state.get("show_low_value", not hide_low_value_default))
        if resume_state
        else not hide_low_value_default
    )

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

        hidden_count = _hidden_node_count(nodes, visible_nodes)
        _render_tree_snapshot(
            state=state,
            current_dir=current_dir,
            nodes=page_items,
            show_low_value=show_low_value,
            hidden_count=hidden_count,
            page_index=page_index,
            total_pages=total_pages,
            console=console,
        )

        choices: list[dict] = []
        if current_dir:
            choices.append(
                {
                    "name": "↩ ..",
                    "value": "control::up",
                }
            )
        for node in page_items:
            marker = _marker_for(state.selection_state(node))
            name = _display_name(node)
            if state.is_dir(node):
                choices.append(
                    {
                        "name": f"▸ {marker} 📁 {name}/",
                        "value": f"node::{node}",
                    }
                )
            else:
                choices.append(
                    {
                        "name": f"{marker} 📄 {name}",
                        "value": f"node::{node}",
                    }
                )
        choices.append(
            {
                "name": "✓ Done and continue",
                "value": "control::done",
            }
        )

        message = f"dir={current_dir or '/'}  page={page_index + 1}/{total_pages}  hidden={hidden_count}"
        try:
            action = action_prompt(message, choices)
        except KeyboardInterrupt:
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            raise

        if action in {"done", "control::done"}:
            break
        if action in {"up", "control::up"}:
            current_dir = state.parent_by_path.get(current_dir, "")
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action == "next":
            page_index += 1
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action == "prev":
            page_index -= 1
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action == "toggle_low_value":
            show_low_value = not show_low_value
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action == "show_all":
            show_low_value = True
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action == "show_filtered":
            show_low_value = False
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action.startswith("space::"):
            selected_value = action.split("::", 1)[1]
            if selected_value.startswith("node::"):
                state.toggle(selected_value.split("::", 1)[1])
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action.startswith("toggle::"):
            state.toggle(action.split("::", 1)[1])
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action.startswith("enter::"):
            selected_value = action.split("::", 1)[1]
            if selected_value == "control::done":
                break
            if selected_value == "control::up":
                current_dir = state.parent_by_path.get(current_dir, "")
                page_index = 0
                _checkpoint_tree_state(
                    state=state,
                    current_dir=current_dir,
                    page_index=page_index,
                    show_low_value=show_low_value,
                    checkpoint_callback=checkpoint_callback,
                )
                continue
            if selected_value.startswith("node::"):
                node = selected_value.split("::", 1)[1]
                if state.is_dir(node):
                    current_dir = node
                else:
                    state.toggle(node)
            else:
                current_dir = selected_value
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue
        if action.startswith("node::"):
            node = action.split("::", 1)[1]
            if state.is_dir(node):
                current_dir = node
            else:
                state.toggle(node)
            page_index = 0
            _checkpoint_tree_state(
                state=state,
                current_dir=current_dir,
                page_index=page_index,
                show_low_value=show_low_value,
                checkpoint_callback=checkpoint_callback,
            )
            continue

        _checkpoint_tree_state(
            state=state,
            current_dir=current_dir,
            page_index=page_index,
            show_low_value=show_low_value,
            checkpoint_callback=checkpoint_callback,
        )

    return state.selected_files & set(candidates)


def _checkpoint_tree_state(
    state: TreeSelectionState,
    current_dir: str,
    page_index: int,
    show_low_value: bool,
    checkpoint_callback: Callable[[dict], None] | None,
) -> None:
    if checkpoint_callback is None:
        return
    checkpoint_callback(
        {
            "selected_paths": sorted(state.selected_files),
            "current_dir": current_dir,
            "page_index": page_index,
            "show_low_value": show_low_value,
        }
    )


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
    """Prompt with Enter-expand and Space-toggle semantics."""
    values = [(item["value"], item["name"]) for item in choices]
    radio = RadioList(values)

    kb = KeyBindings()

    @kb.add("enter", eager=True)
    @kb.add("c-m", eager=True)
    def _on_enter(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result=f"enter::{_radio_cursor_value(radio, values)}")

    @kb.add(" ", eager=True)
    def _on_space(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result=f"space::{_radio_cursor_value(radio, values)}")

    @kb.add("right", eager=True)
    def _on_right(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result=f"enter::{_radio_cursor_value(radio, values)}")

    @kb.add("left", eager=True)
    def _on_left(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="up")

    @kb.add("b", eager=True)
    @kb.add("h", eager=True)
    def _on_up_alias(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="up")

    @kb.add("n", eager=True)
    def _on_next(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="next")

    @kb.add("p", eager=True)
    def _on_prev(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="prev")

    @kb.add("a", eager=True)
    def _on_all(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="show_all")

    @kb.add("f", eager=True)
    def _on_filtered(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="show_filtered")

    @kb.add("q", eager=True)
    @kb.add("escape", eager=True)
    def _on_done(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result="done")

    root = HSplit(
        [
            Window(content=FormattedTextControl(text=message), height=1),
            Window(height=1, char="-"),
            radio,
            Window(
                content=FormattedTextControl(text=_TREE_ACTION_HINT),
                height=1,
            ),
        ]
    )
    app = Application(
        layout=Layout(root, focused_element=radio),
        key_bindings=kb,
        full_screen=False,
    )
    result = app.run()
    return result or "done"


def _radio_cursor_value(radio: RadioList, values: list[tuple[str, str]]) -> str:
    """Return highlighted value instead of checked value."""
    index = int(getattr(radio, "_selected_index", 0))
    index = max(0, min(index, len(values) - 1))
    return values[index][0]


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
        return "●"
    if state == SelectionState.PARTIAL:
        return "◐"
    return "○"


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


def _render_stage3_banner(console: Console, rows: list[PathReviewRow]) -> None:
    tier1 = len([row for row in rows if row.tier == "tier1"])
    tier2 = len([row for row in rows if row.tier == "tier2"])
    text = Text()
    text.append("Stage 3 Tree Review", style="bold cyan")
    text.append("  ")
    text.append(f"tier1={tier1}", style="green")
    text.append("  ")
    text.append(f"tier2={tier2}", style="blue")
    console.print(Panel(text, border_style="cyan"))


def _render_tree_snapshot(
    state: TreeSelectionState,
    current_dir: str,
    nodes: list[str],
    show_low_value: bool,
    hidden_count: int,
    page_index: int,
    total_pages: int,
    console: Console,
) -> None:
    tree = Tree(
        Text(f"{current_dir or '/'}", style="bold cyan"),
        guide_style="dim",
    )
    for node in nodes:
        marker = _marker_for(state.selection_state(node))
        name = _display_name(node)
        if state.is_dir(node):
            style = "cyan" if marker != "○" else "bright_black"
            tree.add(Text(f"{marker} {name}/", style=style))
        else:
            style = "green" if marker == "●" else "white"
            tree.add(Text(f"{marker} {name}", style=style))

    footer = Text()
    footer.append("mode=", style="dim")
    footer.append("all", style="yellow" if show_low_value else "dim")
    footer.append("/", style="dim")
    footer.append("filtered", style="yellow" if not show_low_value else "dim")
    footer.append("  ", style="dim")
    footer.append(f"hidden={hidden_count}", style="yellow")
    footer.append("  ", style="dim")
    footer.append(f"page={page_index + 1}/{total_pages}", style="blue")
    console.print(
        Panel(tree, border_style="blue", title="Directory Tree", subtitle=footer)
    )


def _apply_ai_directory_decisions(
    candidates: list[str],
    defaults: set[str],
    ai_directory_decision_fn: Callable[[str, list[str], list[str]], dict[str, object]],
) -> tuple[set[str], list[dict[str, object]]]:
    state = TreeSelectionState.from_paths(candidates, selected_files=defaults)
    selected = set(defaults)
    decisions: list[dict[str, object]] = []

    current_level = [item for item in state.children("") if state.is_dir(item)]
    while current_level:
        sorted_level = sorted(current_level)
        payload_by_directory: dict[str, dict[str, object]] = {}

        with ThreadPoolExecutor(max_workers=max(1, len(sorted_level))) as executor:
            future_by_directory = {
                directory: executor.submit(
                    ai_directory_decision_fn,
                    directory,
                    [item for item in state.children(directory) if state.is_dir(item)],
                    sorted(state.descendant_files(directory))[:8],
                )
                for directory in sorted_level
            }
            for directory in sorted_level:
                payload_by_directory[directory] = future_by_directory[
                    directory
                ].result()

        next_level: list[str] = []
        for directory in sorted_level:
            child_dirs = [
                item for item in state.children(directory) if state.is_dir(item)
            ]
            payload = payload_by_directory[directory]
            decision = str(payload.get("decision", "not_sure")).lower()
            descendants = state.descendant_files(directory)

            if decision == "keep":
                selected.update(descendants)
            elif decision == "drop":
                selected.difference_update(descendants)
            else:
                decision = "not_sure"

            decisions.append(
                {
                    "directory": directory,
                    "decision": decision,
                    "confidence": float(payload.get("confidence", 0.0)),
                    "reason": str(payload.get("reason", "")),
                }
            )
            next_level.extend(child_dirs)

        current_level = next_level

    return selected, decisions


def _render_ai_dfs_summary(
    console: Console, decisions: list[dict[str, object]]
) -> None:
    if not decisions:
        return
    keep = len([item for item in decisions if item["decision"] == "keep"])
    drop = len([item for item in decisions if item["decision"] == "drop"])
    unsure = len([item for item in decisions if item["decision"] == "not_sure"])
    text = Text()
    text.append("AI DFS pass completed", style="bold cyan")
    text.append("  ")
    text.append(f"keep={keep}", style="green")
    text.append("  ")
    text.append(f"drop={drop}", style="red")
    text.append("  ")
    text.append(f"not_sure={unsure}", style="yellow")
    console.print(Panel(text, border_style="magenta"))
