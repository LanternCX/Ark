"""Stage 1 suffix review defaults and interactive helpers."""

from dataclasses import dataclass
from typing import Callable

import questionary
from rich.console import Console
from rich.table import Table


@dataclass(frozen=True)
class SuffixReviewRow:
    """Single suffix decision item shown in stage 1 review."""

    ext: str
    label: str
    tag: str
    confidence: float
    reason: str


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
        table.add_row(row.ext, row.label, row.tag, f"{row.confidence:.2f}", row.reason)
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

    choices = [
        {
            "name": (
                f"{row.ext:8} | {row.label:4} | {row.tag:12} | "
                f"conf={row.confidence:.2f} | {row.reason}"
            ),
            "value": row.ext,
        }
        for row in rows
    ]

    prompt_fn = checkbox_prompt or _default_checkbox_prompt
    selected = prompt_fn("Suffix whitelist selection", choices, defaults)
    return set(selected)


def _default_checkbox_prompt(
    message: str, choices: list[dict], default: list[str]
) -> list[str]:
    """Default checkbox prompt using questionary."""
    result = questionary.checkbox(
        message=message, choices=choices, default=default
    ).ask()
    return result or []
