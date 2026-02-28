"""Stage 3 final review helpers."""

from dataclasses import dataclass
from typing import Callable

import questionary
from rich.console import Console
from rich.table import Table


@dataclass(frozen=True)
class PathReviewRow:
    """Single path candidate shown in final backup review."""

    path: str
    tier: str
    size_bytes: int
    reason: str
    confidence: float


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
    confirm_prompt: Callable[[str, bool], bool] | None = None,
    console: Console | None = None,
) -> set[str]:
    """Run final TUI review for backup path selection."""
    filtered_rows = [row for row in rows if row.tier in {"tier1", "tier2"}]
    render_stage3_table(filtered_rows, console=console)

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

    checkbox_fn = checkbox_prompt or _default_checkbox_prompt
    selected = checkbox_fn("Final backup selection", choices, defaults)

    confirm_fn = confirm_prompt or _default_confirm_prompt
    approved = confirm_fn("Proceed with backup execution?", True)
    if not approved:
        return set()
    return set(selected)


def _default_checkbox_prompt(
    message: str, choices: list[dict], default: list[str]
) -> list[str]:
    """Default checkbox implementation."""
    result = questionary.checkbox(
        message=message, choices=choices, default=default
    ).ask()
    return result or []


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
