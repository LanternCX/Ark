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


def classify_suffix_category(ext: str) -> str:
    """Classify extension into stage-1 category buckets."""
    value = ext.lower()
    if value in {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".md",
        ".rtf",
    }:
        return "Document"
    if value in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"}:
        return "Image"
    if value in {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".go",
        ".rs",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    }:
        return "Code"
    if value in {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}:
        return "Archive"
    if value in {".mp4", ".mov", ".mkv", ".mp3", ".wav", ".flac"}:
        return "Media"
    if value in {".exe", ".msi", ".dmg", ".pkg", ".app", ".apk"}:
        return "Executable"
    if value in {".tmp", ".cache", ".log", ".bak", ".swp", ".part"}:
        return "Temp/Cache"
    return "Other"


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

    choices = flatten_grouped_suffix_choices(group_suffix_rows(rows))

    prompt_fn = checkbox_prompt or _default_checkbox_prompt
    selected = prompt_fn("Suffix whitelist selection", choices, defaults)
    return {item for item in selected if not str(item).startswith("header::")}


def _default_checkbox_prompt(
    message: str, choices: list[dict], default: list[str]
) -> list[str]:
    """Default checkbox prompt using questionary."""
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
