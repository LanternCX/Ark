"""Run backup pipeline orchestration."""

from typing import Callable

from ark.tui.stage1_review import SuffixReviewRow, run_stage1_review
from ark.tui.stage3_review import PathReviewRow, run_stage3_review


def run_backup_pipeline(
    target: str,
    dry_run: bool,
    stage1_review_fn: Callable[[list[SuffixReviewRow]], set[str]] | None = None,
    stage3_review_fn: Callable[[list[PathReviewRow]], set[str]] | None = None,
) -> list[str]:
    """Run staged review flow and return progress logs."""
    logs: list[str] = [
        "Stage 1: Suffix Screening",
    ]

    suffix_rows = _sample_suffix_rows()
    review_stage1 = stage1_review_fn or run_stage1_review
    whitelist = review_stage1(suffix_rows)
    logs.append(f"Whitelist size: {len(whitelist)}")

    logs.append("Stage 2: Path Tiering")
    path_rows = _sample_path_rows()
    logs.append(f"Tier candidates: {len(path_rows)}")

    logs.append("Stage 3: Final Review and Backup")
    review_stage3 = stage3_review_fn or run_stage3_review
    selected_paths = review_stage3(path_rows)
    logs.append(f"Selected paths: {len(selected_paths)}")
    logs.append(f"Target: {target}")
    logs.append(f"Dry run: {dry_run}")

    if dry_run:
        logs.append("Dry run complete. No files copied.")
    else:
        logs.append("Backup execution placeholder. Copy engine integration pending.")

    return logs


def _sample_suffix_rows() -> list[SuffixReviewRow]:
    return [
        SuffixReviewRow(
            ext=".pdf",
            label="keep",
            tag="document",
            confidence=0.93,
            reason="Likely personal or business document",
        ),
        SuffixReviewRow(
            ext=".jpg",
            label="keep",
            tag="media",
            confidence=0.90,
            reason="Likely personal photo",
        ),
        SuffixReviewRow(
            ext=".tmp",
            label="drop",
            tag="cache",
            confidence=0.91,
            reason="Likely temporary cache artifact",
        ),
    ]


def _sample_path_rows() -> list[PathReviewRow]:
    return [
        PathReviewRow(
            path="C:/Users/me/Documents/report.pdf",
            tier="tier1",
            size_bytes=81234,
            reason="High-value user document path",
            confidence=0.93,
        ),
        PathReviewRow(
            path="C:/Users/me/Pictures/holiday.jpg",
            tier="tier1",
            size_bytes=4_202_444,
            reason="Personal media with likely irreplaceable value",
            confidence=0.89,
        ),
        PathReviewRow(
            path="C:/Users/me/Downloads/archive.zip",
            tier="tier2",
            size_bytes=132_100_230,
            reason="Potentially useful archive requiring manual confirmation",
            confidence=0.64,
        ),
    ]
