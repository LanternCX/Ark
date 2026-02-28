"""Run backup pipeline orchestration."""

from pathlib import Path
from typing import Callable

from ark.backup.executor import mirror_copy_one
from ark.decision.tiering import classify_tier
from ark.state.backup_run_store import BackupRunStore
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
    progress_callback: Callable[[str], None] | None = None,
    run_store: BackupRunStore | None = None,
    run_id: str | None = None,
    resume: bool = False,
) -> list[str]:
    """Run staged review flow and return progress logs."""
    progress = progress_callback or (lambda _message: None)
    normalized_source_roots = [str(item) for item in (source_roots or [])]

    resume_state: dict = {}
    if run_store:
        if resume and run_id:
            loaded = run_store.load_run(run_id)
            resume_state = dict(loaded.get("checkpoints", {}))
            run_store.mark_status(run_id, "running")
        elif not run_id:
            run_id = run_store.create_run(
                target=target,
                source_roots=normalized_source_roots,
                dry_run=dry_run,
            )

    def checkpoint(stage: str, payload: dict) -> None:
        if run_store and run_id:
            run_store.save_checkpoint(run_id, stage=stage, payload=payload)

    try:
        files_by_root = _collect_files_by_root(
            source_roots,
            progress_callback=progress,
            resume_payload=resume_state.get("scan") if resume else None,
            checkpoint_callback=lambda payload: checkpoint("scan", payload),
        )
    except KeyboardInterrupt:
        if run_store and run_id:
            run_store.mark_status(run_id, "paused")
        raise

    has_configured_sources = bool(source_roots)
    using_sample_data = not files_by_root and not has_configured_sources

    logs: list[str] = [
        "Stage 1: Suffix Screening",
    ]
    if resume and run_id:
        logs.append(f"Resumed run: {run_id}")
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
    checkpoint("stage1", {"whitelist": sorted(whitelist)})
    progress(f"[stage1] whitelist={len(whitelist)}")
    logs.append(f"Whitelist size: {len(whitelist)}")

    logs.append("Stage 2: Path Tiering")
    path_rows = _build_stage2_rows(
        files_by_root,
        whitelist,
        use_sample_rows=using_sample_data,
        path_risk_fn=path_risk_fn,
        send_full_path_to_ai=send_full_path_to_ai,
        progress_callback=progress,
        resume_payload=resume_state.get("stage2") if resume else None,
        checkpoint_callback=lambda payload: checkpoint("stage2", payload),
    )
    progress(f"[ai] candidates={len(path_rows)}")
    logs.append(f"Tier candidates: {len(path_rows)}")

    logs.append("Stage 3: Final Review and Backup")
    if stage3_review_fn:
        selected_paths = stage3_review_fn(path_rows)
    else:
        selected_paths = run_stage3_review(
            path_rows,
            hide_low_value_default=(ai_prune_mode == "hide_low_value"),
            resume_state=resume_state.get("review") if resume else None,
            checkpoint_callback=lambda payload: checkpoint("review", payload),
        )
    checkpoint("review", {"selected_paths": sorted(selected_paths)})
    progress(f"[review] selected={len(selected_paths)}")
    logs.append(f"Selected paths: {len(selected_paths)}")
    logs.append(f"Target: {target}")
    logs.append(f"Dry run: {dry_run}")

    if dry_run:
        checkpoint("copy", {"copied_paths": [], "copy_complete": True})
        progress("[copy] dry run complete")
        logs.append("Dry run complete. No files copied.")
    else:
        copied_count = _copy_selected_paths(
            files_by_root=files_by_root,
            selected_paths=selected_paths,
            target_root=Path(target),
            progress_callback=progress,
            resume_payload=resume_state.get("copy") if resume else None,
            checkpoint_callback=lambda payload: checkpoint("copy", payload),
        )
        progress(f"[copy] copied={copied_count}")
        logs.append(f"Copied files: {copied_count}")

    if run_store and run_id:
        run_store.mark_status(run_id, "completed")

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
    progress_callback: Callable[[str], None] | None = None,
    resume_payload: dict | None = None,
    checkpoint_callback: Callable[[dict], None] | None = None,
) -> dict[Path, list[Path]]:
    progress = progress_callback or (lambda _message: None)
    if not source_roots:
        return {}

    if resume_payload and resume_payload.get("scan_complete"):
        restored: dict[Path, list[Path]] = {}
        raw = resume_payload.get("files_by_root", {})
        for root, entries in raw.items():
            restored[Path(root)] = [Path(item) for item in entries]
        progress("[scan] restored completed scan checkpoint")
        return restored

    resumed_seen: set[str] = set()
    if resume_payload:
        raw = resume_payload.get("files_by_root", {})
        for entries in raw.values():
            resumed_seen.update(str(item) for item in entries)

    files_by_root: dict[Path, list[Path]] = {}
    discovered = 0
    for root in source_roots:
        if not root.exists() or not root.is_dir():
            continue
        progress(f"[scan] scanning root={root}")
        files = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            text = str(path)
            if text in resumed_seen:
                continue
            files.append(path)
            discovered += 1
            if discovered % 200 == 0:
                progress(f"[scan] discovered={discovered} current={path.parent}")
                if checkpoint_callback:
                    merged = {
                        str(item_root): [str(item) for item in items]
                        for item_root, items in files_by_root.items()
                    }
                    merged.setdefault(str(root), [])
                    merged[str(root)].extend(str(item) for item in files)
                    checkpoint_callback(
                        {
                            "files_by_root": merged,
                            "scan_complete": False,
                        }
                    )
        files_by_root[root] = sorted(files, key=lambda item: str(item))

    if checkpoint_callback:
        checkpoint_callback(
            {
                "files_by_root": {
                    str(root): [str(item) for item in paths]
                    for root, paths in files_by_root.items()
                },
                "scan_complete": True,
            }
        )
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
    progress_callback: Callable[[str], None] | None = None,
    resume_payload: dict | None = None,
    checkpoint_callback: Callable[[dict], None] | None = None,
) -> list[PathReviewRow]:
    progress = progress_callback or (lambda _message: None)
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
    path_risk_lookup: dict[str, dict[str, object]] = {}
    if resume_payload and isinstance(resume_payload.get("risk_lookup"), dict):
        raw_lookup = dict(resume_payload.get("risk_lookup", {}))
        path_risk_lookup = {
            str(key): dict(value)
            for key, value in raw_lookup.items()
            if isinstance(value, dict)
        }

    if path_risk_fn:
        batch_size = 50
        start_index = int(resume_payload.get("next_index", 0)) if resume_payload else 0
        for index in range(start_index, len(candidate_inputs), batch_size):
            batch = candidate_inputs[index : index + batch_size]
            if not batch:
                continue
            progress(
                f"[ai:path] querying batch={index // batch_size + 1} size={len(batch)}"
            )
            update = path_risk_fn(batch)
            path_risk_lookup.update(update)
            if checkpoint_callback:
                checkpoint_callback(
                    {
                        "next_index": index + len(batch),
                        "risk_lookup": path_risk_lookup,
                    }
                )

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
    files_by_root: dict[Path, list[Path]],
    selected_paths: set[str],
    target_root: Path,
    progress_callback: Callable[[str], None] | None = None,
    resume_payload: dict | None = None,
    checkpoint_callback: Callable[[dict], None] | None = None,
) -> int:
    progress = progress_callback or (lambda _message: None)
    selected_lookup = set(selected_paths)
    already_copied = {
        str(path)
        for path in (resume_payload.get("copied_paths", []) if resume_payload else [])
    }
    copied = 0

    for src_root, paths in files_by_root.items():
        for src_path in paths:
            src_path_str = str(src_path)
            if src_path_str not in selected_lookup:
                continue
            if src_path_str in already_copied:
                continue
            progress(f"[copy] copying {src_path_str}")
            mirror_copy_one(src_root=src_root, src_path=src_path, dst_root=target_root)
            copied += 1
            already_copied.add(src_path_str)
            if checkpoint_callback:
                checkpoint_callback(
                    {
                        "copied_paths": sorted(already_copied),
                        "copy_complete": False,
                    }
                )

    if checkpoint_callback:
        checkpoint_callback(
            {
                "copied_paths": sorted(already_copied),
                "copy_complete": True,
            }
        )

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
