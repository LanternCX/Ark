"""Run backup pipeline orchestration."""

from pathlib import Path
from typing import Callable

from ark.backup.executor import mirror_copy_one
from ark.decision.tiering import classify_tier
from ark.signals.extractor import extension_score
from ark.tui.stage1_review import SuffixReviewRow, run_stage1_review
from ark.tui.stage3_review import PathReviewRow, run_stage3_review


def run_backup_pipeline(
    target: str,
    dry_run: bool,
    source_roots: list[Path] | None = None,
    stage1_review_fn: Callable[[list[SuffixReviewRow]], set[str]] | None = None,
    stage3_review_fn: Callable[[list[PathReviewRow]], set[str]] | None = None,
    suffix_risk_fn: Callable[[list[str]], dict[str, dict[str, object]]] | None = None,
    path_risk_fn: Callable[[list[str]], dict[str, dict[str, object]]] | None = None,
    send_full_path_to_ai: bool = False,
    ai_prune_mode: str = "hide_low_value",
) -> list[str]:
    """Run staged review flow and return progress logs."""
    files_by_root = _collect_files_by_root(source_roots)
    has_configured_sources = bool(source_roots)
    using_sample_data = not files_by_root and not has_configured_sources

    logs: list[str] = [
        "Stage 1: Suffix Screening",
    ]
    if using_sample_data:
        logs.append(
            "No valid source files discovered from configured roots; using sample data."
        )
    elif has_configured_sources and not files_by_root:
        logs.append(
            "No files discovered under configured source roots; review source paths in Settings."
        )

    suffix_rows = _build_stage1_rows(
        files_by_root,
        use_sample_rows=using_sample_data,
        suffix_risk_fn=suffix_risk_fn,
    )
    review_stage1 = stage1_review_fn or run_stage1_review
    whitelist = review_stage1(suffix_rows)
    logs.append(f"Whitelist size: {len(whitelist)}")

    logs.append("Stage 2: Path Tiering")
    path_rows = _build_stage2_rows(
        files_by_root,
        whitelist,
        use_sample_rows=using_sample_data,
        path_risk_fn=path_risk_fn,
        send_full_path_to_ai=send_full_path_to_ai,
    )
    logs.append(f"Tier candidates: {len(path_rows)}")

    logs.append("Stage 3: Final Review and Backup")
    if stage3_review_fn:
        selected_paths = stage3_review_fn(path_rows)
    else:
        selected_paths = run_stage3_review(
            path_rows,
            hide_low_value_default=(ai_prune_mode == "hide_low_value"),
        )
    logs.append(f"Selected paths: {len(selected_paths)}")
    logs.append(f"Target: {target}")
    logs.append(f"Dry run: {dry_run}")

    if dry_run:
        logs.append("Dry run complete. No files copied.")
    else:
        copied_count = _copy_selected_paths(
            files_by_root=files_by_root,
            selected_paths=selected_paths,
            target_root=Path(target),
        )
        logs.append(f"Copied files: {copied_count}")

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
    home = Path.home()
    return [
        PathReviewRow(
            path=str(home / "Documents" / "report.pdf"),
            tier="tier1",
            size_bytes=81234,
            reason="High-value user document path",
            confidence=0.93,
        ),
        PathReviewRow(
            path=str(home / "Pictures" / "holiday.jpg"),
            tier="tier1",
            size_bytes=4_202_444,
            reason="Personal media with likely irreplaceable value",
            confidence=0.89,
        ),
        PathReviewRow(
            path=str(home / "Downloads" / "archive.zip"),
            tier="tier2",
            size_bytes=132_100_230,
            reason="Potentially useful archive requiring manual confirmation",
            confidence=0.64,
        ),
    ]


def _collect_files_by_root(
    source_roots: list[Path] | None,
) -> dict[Path, list[Path]]:
    if not source_roots:
        return {}

    files_by_root: dict[Path, list[Path]] = {}
    for root in source_roots:
        if not root.exists() or not root.is_dir():
            continue
        files = [path for path in root.rglob("*") if path.is_file()]
        files_by_root[root] = sorted(files, key=lambda item: str(item))
    return files_by_root


def _build_stage1_rows(
    files_by_root: dict[Path, list[Path]],
    use_sample_rows: bool,
    suffix_risk_fn: Callable[[list[str]], dict[str, dict[str, object]]] | None = None,
) -> list[SuffixReviewRow]:
    if not files_by_root:
        return _sample_suffix_rows() if use_sample_rows else []

    discovered_extensions: set[str] = set()
    for paths in files_by_root.values():
        for path in paths:
            if not path.suffix:
                continue
            discovered_extensions.add(path.suffix.lower())

    if not discovered_extensions:
        return _sample_suffix_rows() if use_sample_rows else []

    rows: list[SuffixReviewRow] = []
    risk_overrides = (
        suffix_risk_fn(sorted(discovered_extensions)) if suffix_risk_fn else {}
    )
    for ext in sorted(discovered_extensions):
        label, tag, confidence, reason = _stage1_heuristic(ext)
        label, tag, confidence, reason = _apply_suffix_risk_override(
            ext,
            label,
            tag,
            confidence,
            reason,
            risk_overrides,
        )
        rows.append(
            SuffixReviewRow(
                ext=ext,
                label=label,
                tag=tag,
                confidence=confidence,
                reason=reason,
            )
        )
    return rows


def _stage1_heuristic(ext: str) -> tuple[str, str, float, str]:
    keep_exts = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".jpg",
        ".jpeg",
        ".png",
        ".md",
        ".txt",
    }
    if ext in keep_exts:
        return ("keep", "likely-user-data", 0.85, "Likely user-created content")
    return ("drop", "likely-generated", 0.70, "Likely generated or low-value artifact")


def _build_stage2_rows(
    files_by_root: dict[Path, list[Path]],
    whitelist: set[str],
    use_sample_rows: bool,
    path_risk_fn: Callable[[list[str]], dict[str, dict[str, object]]] | None = None,
    send_full_path_to_ai: bool = False,
) -> list[PathReviewRow]:
    if not files_by_root:
        return _sample_path_rows() if use_sample_rows else []

    candidate_paths: list[Path] = []
    for paths in files_by_root.values():
        for path in paths:
            ext = path.suffix.lower()
            if whitelist and ext not in whitelist:
                continue
            candidate_paths.append(path)

    candidate_inputs = [
        str(path) if send_full_path_to_ai else path.name for path in candidate_paths
    ]
    path_risk_lookup = path_risk_fn(candidate_inputs) if path_risk_fn else {}

    rows: list[PathReviewRow] = []
    for path in candidate_paths:
        signal_score = extension_score(path)
        ai_score = _ai_score_heuristic(path)

        key = str(path) if send_full_path_to_ai else path.name
        override = path_risk_lookup.get(key) or path_risk_lookup.get(str(path))
        ai_risk = "neutral"
        reason = "Local signal + heuristic AI fusion"
        override_confidence = 0.0
        if override:
            ai_risk = str(override.get("risk", "neutral"))
            reason = str(override.get("reason", reason))
            ai_score = float(override.get("score", ai_score))
            override_confidence = float(override.get("confidence", 0.0))

        confidence = max(signal_score, ai_score, override_confidence)
        tier = classify_tier(
            signal_score=signal_score, ai_score=ai_score, confidence=confidence
        )
        rows.append(
            PathReviewRow(
                path=str(path),
                tier=tier,
                size_bytes=path.stat().st_size,
                reason=reason,
                confidence=confidence,
                ai_risk=ai_risk,
            )
        )
    return rows


def _apply_suffix_risk_override(
    ext: str,
    label: str,
    tag: str,
    confidence: float,
    reason: str,
    risk_overrides: dict[str, dict[str, object]],
) -> tuple[str, str, float, str]:
    override = risk_overrides.get(ext)
    if not override:
        return label, tag, confidence, reason

    risk = str(override.get("risk", "neutral"))
    overridden_confidence = float(override.get("confidence", confidence))
    overridden_reason = str(override.get("reason", reason))

    if risk == "high_value":
        return "keep", "ai-high-value", overridden_confidence, overridden_reason
    if risk == "low_value":
        return "drop", "ai-low-value", overridden_confidence, overridden_reason
    return label, tag, overridden_confidence, overridden_reason


def _copy_selected_paths(
    files_by_root: dict[Path, list[Path]], selected_paths: set[str], target_root: Path
) -> int:
    selected_lookup = set(selected_paths)
    copied = 0

    for src_root, paths in files_by_root.items():
        for src_path in paths:
            if str(src_path) not in selected_lookup:
                continue
            mirror_copy_one(src_root=src_root, src_path=src_path, dst_root=target_root)
            copied += 1

    return copied


def _ai_score_heuristic(path: Path) -> float:
    keyword_hits = {"document", "documents", "picture", "pictures", "photo", "desktop"}
    parts = {part.lower() for part in path.parts}
    if parts.intersection(keyword_hits):
        return 0.85
    if path.suffix.lower() in {
        ".pdf",
        ".doc",
        ".docx",
        ".jpg",
        ".jpeg",
        ".png",
        ".md",
        ".txt",
    }:
        return 0.7
    return 0.35
