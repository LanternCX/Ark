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


def test_run_backup_pipeline_applies_suffix_risk_overrides(tmp_path) -> None:
    (tmp_path / "cache.tmp").write_text("cache", encoding="utf-8")
    observed_rows = []

    def fake_stage1_review(rows):
        nonlocal observed_rows
        observed_rows = rows
        return {row.ext for row in rows if row.label == "keep"}

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=lambda _rows: set(),
        suffix_risk_fn=lambda _exts: {
            ".tmp": {
                "risk": "high_value",
                "confidence": 0.95,
                "reason": "Requested by user policy",
            }
        },
    )

    assert len(observed_rows) == 1
    assert observed_rows[0].ext == ".tmp"
    assert observed_rows[0].label == "keep"
    assert "Requested by user policy" in observed_rows[0].reason


def test_run_backup_pipeline_passes_full_paths_to_path_risk_function(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.tmp").write_text("b", encoding="utf-8")
    observed_paths: list[str] = []
    observed_stage3_rows = []

    def fake_path_risk(paths: list[str]) -> dict[str, dict[str, object]]:
        nonlocal observed_paths
        observed_paths = paths
        return {
            paths[1]: {
                "risk": "low_value",
                "confidence": 0.9,
                "reason": "Likely temp file",
                "score": 0.1,
            }
        }

    def fake_stage3_review(rows):
        nonlocal observed_stage3_rows
        observed_stage3_rows = rows
        return set()

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=lambda rows: {row.ext for row in rows},
        stage3_review_fn=fake_stage3_review,
        path_risk_fn=fake_path_risk,
        send_full_path_to_ai=True,
    )

    assert all(str(tmp_path) in item for item in observed_paths)
    row_by_path = {row.path: row for row in observed_stage3_rows}
    low_path = str(tmp_path / "b.tmp")
    assert row_by_path[low_path].ai_risk == "low_value"
    assert "Likely temp" in row_by_path[low_path].reason
