"""Stage 1 suffix review defaults and interactive helpers."""

from dataclasses import dataclass
from typing import Callable

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import CheckboxList
from rich.console import Console
from rich.table import Table

from src.rules.local_rules import suffix_category


@dataclass(frozen=True)
class SuffixReviewRow:
    """Single suffix decision item shown in stage 1 review."""

    ext: str
    label: str
    tag: str
    confidence: float
    reason: str


_CATEGORY_ORDER = [
    "Document",
    "Image",
    "Code",
    "Archive",
    "Media",
    "Executable",
    "Temp/Cache",
    "Other",
]

_STAGE1_ACTION_HINT = "Up/Down=move, Space=toggle, Enter/q/esc=continue"


def classify_suffix_category(ext: str) -> str:
    """Classify extension into stage-1 category buckets."""
    return suffix_category(ext)


def group_suffix_rows(rows: list[SuffixReviewRow]) -> dict[str, list[SuffixReviewRow]]:
    """Group stage-1 rows by category with stable category order."""
    grouped: dict[str, list[SuffixReviewRow]] = {name: [] for name in _CATEGORY_ORDER}
    for row in rows:
        grouped[classify_suffix_category(row.ext)].append(row)
    return {name: values for name, values in grouped.items() if values}


def flatten_grouped_suffix_choices(
    grouped: dict[str, list[SuffixReviewRow]],
) -> list[dict]:
    """Build grouped checkbox choices with category headers."""
    choices: list[dict] = []
    for category in _CATEGORY_ORDER:
        if category not in grouped:
            continue
        rows = grouped[category]
        choices.append(
            {
                "name": f"[{category}]",
                "value": f"header::{category}",
                "disabled": "category",
            }
        )
        for row in rows:
            choices.append(
                {
                    "name": (
                        f"  {row.ext:8} {row.label:4} conf={row.confidence:.2f} {row.reason}"
                    ),
                    "value": row.ext,
                }
            )
    return choices


def build_category_choices(grouped: dict[str, list[SuffixReviewRow]]) -> list[dict]:
    """Build category-level checkbox choices."""
    choices: list[dict] = []
    for category in _CATEGORY_ORDER:
        if category not in grouped:
            continue
        choices.append(
            {
                "name": f"[{category}] ({len(grouped[category])})",
                "value": f"category::{category}",
            }
        )
    return choices


def apply_default_selection(rows: list[dict], threshold: float) -> set[str]:
    """Select extensions that are keep-labeled with enough confidence."""
    selected: set[str] = set()
    for row in rows:
        if (
            row.get("label") == "keep"
            and float(row.get("confidence", 0.0)) >= threshold
        ):
            selected.add(str(row["ext"]))
    return selected


def _marker_for_state(selected_count: int, total_count: int) -> str:
    """Map selection coverage to symbolic marker style."""
    if total_count <= 0 or selected_count <= 0:
        return "○"
    if selected_count >= total_count:
        return "●"
    return "◐"


def _format_category_choice_name(
    category_name: str,
    selected_count: int,
    total_count: int,
) -> str:
    """Render category row with symbolic marker and folder icon."""
    marker = _marker_for_state(selected_count=selected_count, total_count=total_count)
    return f"▸ {marker} 📁 {category_name}/ ({total_count})"


def _format_suffix_choice_name(
    ext: str,
    label: str,
    confidence: float,
    reason: str,
    selected: bool,
) -> str:
    """Render suffix row with symbolic marker and file icon."""
    marker = _marker_for_state(selected_count=1 if selected else 0, total_count=1)
    return f"  {marker} 📄 {ext:8} {label:4} conf={confidence:.2f} {reason}"


def _build_category_children(choices: list[dict]) -> dict[str, set[str]]:
    """Build category to child suffix mapping from prompt choices."""
    category_children: dict[str, set[str]] = {}
    for item in choices:
        value = str(item["value"])
        if not value.startswith("category::"):
            continue
        children = {str(child) for child in item.get("children", [])}
        category_children[value] = children
    return category_children


def _refresh_choice_names(
    choices: list[dict],
    selected_values: set[str],
    category_children: dict[str, set[str]],
) -> None:
    """Refresh category and suffix labels using current selection state."""
    for item in choices:
        value = str(item["value"])
        if value.startswith("category::"):
            category_name = str(item.get("category_name") or value.split("::", 1)[1])
            children = category_children.get(value, set())
            selected_count = len(children & selected_values)
            item["name"] = _format_category_choice_name(
                category_name=category_name,
                selected_count=selected_count,
                total_count=len(children),
            )
            continue

        if str(item.get("kind", "")) == "suffix":
            ext = str(item.get("ext", value))
            label = str(item.get("label", ""))
            confidence = float(item.get("confidence", 0.0))
            reason = str(item.get("reason", ""))
            item["name"] = _format_suffix_choice_name(
                ext=ext,
                label=label,
                confidence=confidence,
                reason=reason,
                selected=value in selected_values,
            )
            continue

        base_name = str(item.setdefault("raw_name", item.get("name", value)))
        marker = _marker_for_state(
            selected_count=1 if value in selected_values else 0,
            total_count=1,
        )
        item["name"] = f"{marker} {base_name}"


def render_stage1_table(
    rows: list[SuffixReviewRow], console: Console | None = None
) -> None:
    """Render a rich table for suffix screening review."""
    ui = console or Console()
    table = Table(title="Stage 1 - Suffix Screening Review")
    table.add_column("Extension")
    table.add_column("AI Label")
    table.add_column("Tag")
    table.add_column("Confidence", justify="right")
    table.add_column("Reason")

    for row in rows:
        category = classify_suffix_category(row.ext)
        style = _style_for_category(category)
        table.add_row(
            row.ext,
            row.label,
            f"{category}/{row.tag}",
            f"{row.confidence:.2f}",
            row.reason,
            style=style,
        )
    ui.print(table)


def run_stage1_review(
    rows: list[SuffixReviewRow],
    threshold: float = 0.8,
    checkbox_prompt: Callable[[str, list[dict], list[str]], list[str]] | None = None,
    console: Console | None = None,
) -> set[str]:
    """Run interactive stage 1 whitelist confirmation."""
    render_stage1_table(rows, console=console)
    normalized_rows = [
        {"ext": row.ext, "label": row.label, "confidence": row.confidence}
        for row in rows
    ]
    defaults = sorted(apply_default_selection(normalized_rows, threshold))
    grouped = group_suffix_rows(rows)
    prompt_fn = checkbox_prompt or _default_checkbox_prompt

    choices: list[dict] = []
    for category in _CATEGORY_ORDER:
        if category not in grouped:
            continue
        suffixes = [row.ext for row in grouped[category]]
        category_value = f"category::{category}"
        choices.append(
            {
                "name": "",
                "value": category_value,
                "children": suffixes,
                "category_name": category,
            }
        )
        for row in grouped[category]:
            choices.append(
                {
                    "name": "",
                    "value": row.ext,
                    "category": category_value,
                    "kind": "suffix",
                    "ext": row.ext,
                    "label": row.label,
                    "confidence": row.confidence,
                    "reason": row.reason,
                }
            )

    category_defaults = [
        f"category::{category}"
        for category in _CATEGORY_ORDER
        if category in grouped
        and all(item.ext in defaults for item in grouped[category])
    ]
    initial_selected = set(defaults + category_defaults)
    category_children = _build_category_children(choices)
    _refresh_choice_names(choices, initial_selected, category_children)
    selected = prompt_fn(
        "Suffix whitelist selection",
        choices,
        sorted(initial_selected),
    )

    selected_set = {str(item) for item in selected}
    selected_exts = {item for item in selected_set if not item.startswith("category::")}
    for category in _CATEGORY_ORDER:
        key = f"category::{category}"
        if key in selected_set and category in grouped:
            selected_exts.update(item.ext for item in grouped[category])

    all_exts = {row.ext for row in rows}
    return selected_exts & all_exts


def _default_checkbox_prompt(
    message: str, choices: list[dict], default: list[str]
) -> list[str]:
    """Default checkbox prompt with explicit done shortcuts."""
    if not choices:
        return []

    category_children = _build_category_children(choices)
    suffix_category: dict[str, str] = {}
    for item in choices:
        value = str(item["value"])
        if value.startswith("category::"):
            continue
        category_value = str(item.get("category", ""))
        if category_value.startswith("category::"):
            suffix_category[value] = category_value

    valid_values = {str(item["value"]) for item in choices}
    initial_selected = {value for value in default if value in valid_values}
    for category_value, children in category_children.items():
        if category_value in initial_selected:
            initial_selected.update(children)
        if children and children.issubset(initial_selected):
            initial_selected.add(category_value)
        else:
            initial_selected.discard(category_value)

    _refresh_choice_names(choices, initial_selected, category_children)
    values = [(str(item["value"]), str(item["name"])) for item in choices]

    checkbox = CheckboxList(
        values=values,
        default_values=[value for value, _ in values if value in initial_selected],
    )

    kb = KeyBindings()

    @kb.add(" ", eager=True)
    def _on_space(event) -> None:  # type: ignore[no-untyped-def]
        nonlocal values
        del event
        value = _checkbox_cursor_value(checkbox, values)
        selected = set(checkbox.current_values)
        if value.startswith("category::"):
            children = category_children.get(value, set())
            if children and children.issubset(selected):
                selected.difference_update(children)
                selected.discard(value)
            else:
                selected.update(children)
                selected.add(value)
        else:
            if value in selected:
                selected.remove(value)
            else:
                selected.add(value)

            parent_category = suffix_category.get(value)
            if parent_category:
                children = category_children.get(parent_category, set())
                if children and children.issubset(selected):
                    selected.add(parent_category)
                else:
                    selected.discard(parent_category)

        for category_value, children in category_children.items():
            if children and children.issubset(selected):
                selected.add(category_value)
            else:
                selected.discard(category_value)

        _refresh_choice_names(choices, selected, category_children)
        values = [(str(item["value"]), str(item["name"])) for item in choices]
        checkbox.values = values
        checkbox.current_values = [item for item, _ in values if item in selected]

    @kb.add("enter", eager=True)
    @kb.add("c-m", eager=True)
    @kb.add("q", eager=True)
    @kb.add("escape", eager=True)
    def _on_done(event) -> None:  # type: ignore[no-untyped-def]
        event.app.exit(result=list(checkbox.current_values))

    root = HSplit(
        [
            Window(content=FormattedTextControl(text=message), height=1),
            Window(height=1, char="-"),
            checkbox,
            Window(content=FormattedTextControl(text=_STAGE1_ACTION_HINT), height=1),
        ]
    )
    app = Application(
        layout=Layout(root, focused_element=checkbox),
        key_bindings=kb,
        full_screen=False,
    )
    result = app.run()
    return list(result or [])


def _checkbox_cursor_value(
    checkbox: CheckboxList, values: list[tuple[str, str]]
) -> str:
    index = int(getattr(checkbox, "_selected_index", 0))
    index = max(0, min(index, len(values) - 1))
    return values[index][0]


def _style_for_category(category: str) -> str:
    styles = {
        "Document": "green",
        "Image": "cyan",
        "Code": "blue",
        "Archive": "magenta",
        "Media": "bright_cyan",
        "Executable": "red",
        "Temp/Cache": "yellow",
        "Other": "white",
    }
    return styles.get(category, "white")
