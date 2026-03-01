import src.pipeline.run_backup as run_backup_module
from src.pipeline.run_backup import run_backup_pipeline
from src.state.backup_run_store import BackupRunStore


def test_run_backup_pipeline_executes_mirror_copy_for_selected_paths(tmp_path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_file = src_root / "docs" / "a.txt"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("hello", encoding="utf-8")

    target = tmp_path / "backup"

    def fake_stage1_review(rows):
        return {".txt"}

    def fake_stage3_review(rows):
        return {row.path for row in rows}

    run_backup_pipeline(
        target=str(target),
        dry_run=False,
        source_roots=[src_root],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert (target / "src" / "docs" / "a.txt").exists()


def test_run_backup_pipeline_emits_progress_messages(tmp_path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / "docs").mkdir()
    (src_root / "docs" / "a.txt").write_text("hello", encoding="utf-8")
    progress: list[str] = []

    run_backup_pipeline(
        target=str(tmp_path / "backup"),
        dry_run=True,
        source_roots=[src_root],
        stage1_review_fn=lambda rows: {row.ext for row in rows},
        stage3_review_fn=lambda rows: {row.path for row in rows},
        progress_callback=progress.append,
    )

    joined = "\n".join(progress)
    assert "scan" in joined.lower()
    assert "ai" in joined.lower()
    assert "copy" in joined.lower() or "dry run" in joined.lower()


def test_run_backup_pipeline_can_resume_from_saved_selection_state(tmp_path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / "docs").mkdir()
    first = src_root / "docs" / "a.txt"
    second = src_root / "docs" / "b.txt"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")

    store = BackupRunStore(tmp_path / "runs")
    run_id = store.create_run(
        target=str(tmp_path / "backup"),
        source_roots=[str(src_root)],
        dry_run=True,
    )
    store.save_checkpoint(
        run_id,
        stage="review",
        payload={
            "selected_paths": [str(first)],
            "current_dir": str(src_root / "docs"),
            "page_index": 0,
            "show_low_value": True,
        },
    )
    store.mark_status(run_id, "paused")

    logs = run_backup_pipeline(
        target=str(tmp_path / "backup"),
        dry_run=True,
        source_roots=[src_root],
        stage1_review_fn=lambda rows: {row.ext for row in rows},
        stage3_review_fn=lambda rows: {row.path for row in rows},
        run_store=store,
        run_id=run_id,
        resume=True,
    )

    assert any("resumed" in line.lower() for line in logs)


def test_run_backup_pipeline_passes_directory_decision_fn_to_stage3(
    tmp_path, monkeypatch
) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / "docs").mkdir()
    (src_root / "docs" / "a.txt").write_text("hello", encoding="utf-8")

    observed: dict[str, object] = {}

    def fake_stage3_review(rows, **kwargs):
        observed.update(kwargs)
        return {row.path for row in rows}

    monkeypatch.setattr(run_backup_module, "run_stage3_review", fake_stage3_review)

    run_backup_pipeline(
        target=str(tmp_path / "backup"),
        dry_run=True,
        source_roots=[src_root],
        stage1_review_fn=lambda rows: {row.ext for row in rows},
        directory_decision_fn=lambda _d, _c, _s: {
            "decision": "not_sure",
            "confidence": 0.0,
            "reason": "test",
        },
    )

    assert callable(observed["ai_directory_decision_fn"])


def test_run_backup_pipeline_prunes_local_noise_directories_before_stage1(
    tmp_path,
) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / ".venv" / "lib").mkdir(parents=True)
    (src_root / ".venv" / "lib" / "ignore.py").write_text(
        "print('x')", encoding="utf-8"
    )
    (src_root / "app").mkdir()
    (src_root / "app" / "keep.txt").write_text("ok", encoding="utf-8")

    observed_rows = []

    def fake_stage1_review(rows):
        nonlocal observed_rows
        observed_rows = rows
        return {row.ext for row in rows if row.label == "keep"}

    run_backup_pipeline(
        target=str(tmp_path / "backup"),
        dry_run=True,
        source_roots=[src_root],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=lambda _rows: set(),
    )

    discovered_exts = {row.ext for row in observed_rows}
    assert ".txt" in discovered_exts
    assert ".py" not in discovered_exts
