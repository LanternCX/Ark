from pathlib import Path

from ark.pipeline import run_backup as run_backup_module
from ark.pipeline.run_backup import run_backup_pipeline


def test_run_backup_pipeline_uses_stage_reviews() -> None:
    stage1_called = False
    stage3_called = False

    def fake_stage1_review(rows):
        nonlocal stage1_called
        stage1_called = True
        assert rows
        return {".pdf", ".docx"}

    def fake_stage3_review(rows):
        nonlocal stage3_called
        stage3_called = True
        assert rows
        return {rows[0].path}

    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert stage1_called is True
    assert stage3_called is True
    assert any("Whitelist size: 2" in line for line in logs)
    assert any("Selected paths: 1" in line for line in logs)


def test_run_backup_pipeline_builds_stage1_rows_from_source_files(tmp_path) -> None:
    (tmp_path / "notes.md").write_text("doc", encoding="utf-8")
    (tmp_path / "trace.log").write_text("trace", encoding="utf-8")

    observed_extensions: set[str] = set()

    def fake_stage1_review(rows):
        nonlocal observed_extensions
        observed_extensions = {row.ext for row in rows}
        return {".md"}

    def fake_stage3_review(rows):
        return {row.path for row in rows}

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert ".md" in observed_extensions
    assert ".log" in observed_extensions


def test_run_backup_pipeline_filters_stage2_candidates_by_whitelist(tmp_path) -> None:
    (tmp_path / "notes.md").write_text("doc", encoding="utf-8")
    (tmp_path / "cache.tmp").write_text("cache", encoding="utf-8")

    observed_paths: list[str] = []

    def fake_stage1_review(rows):
        assert {row.ext for row in rows} == {".md", ".tmp"}
        return {".md"}

    def fake_stage3_review(rows):
        nonlocal observed_paths
        observed_paths = [row.path for row in rows]
        return set()

    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert len(observed_paths) == 1
    assert observed_paths[0].endswith("notes.md")
    assert any("Tier candidates: 1" in line for line in logs)


def test_sample_path_rows_use_current_home_directory() -> None:
    rows = run_backup_module._sample_path_rows()

    home_prefix = str(Path.home())
    assert all(row.path.startswith(home_prefix) for row in rows)


def test_run_backup_pipeline_logs_when_using_sample_data() -> None:
    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=None,
        stage1_review_fn=lambda _rows: {".pdf", ".jpg"},
        stage3_review_fn=lambda rows: {row.path for row in rows[:1]},
    )

    assert any("using sample data" in line.lower() for line in logs)


def test_run_backup_pipeline_does_not_use_sample_data_when_sources_configured_but_invalid() -> (
    None
):
    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[Path("/path/that/does/not/exist")],
        stage1_review_fn=lambda _rows: set(),
        stage3_review_fn=lambda _rows: set(),
    )

    assert not any("using sample data" in line.lower() for line in logs)
    assert any("no files discovered" in line.lower() for line in logs)
