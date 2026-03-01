from pathlib import Path

from src.pipeline import run_backup as run_backup_module
from src.pipeline.run_backup import run_backup_pipeline


def test_run_backup_pipeline_uses_stage_reviews() -> None:
    stage1_called = False
    final_review_called = False

    def fake_stage1_review(rows):
        nonlocal stage1_called
        stage1_called = True
        assert rows
        return {".pdf", ".docx"}

    def fake_final_review(rows):
        nonlocal final_review_called
        final_review_called = True
        assert rows
        return {rows[0].path}

    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        stage1_review_fn=fake_stage1_review,
        final_review_fn=fake_final_review,
    )

    assert stage1_called is True
    assert final_review_called is True
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

    def fake_final_review(rows):
        return {row.path for row in rows}

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        final_review_fn=fake_final_review,
    )

    assert ".md" in observed_extensions
    assert ".log" in observed_extensions


def test_run_backup_pipeline_filters_internal_tiering_candidates_by_whitelist(
    tmp_path,
) -> None:
    (tmp_path / "notes.md").write_text("doc", encoding="utf-8")
    (tmp_path / "cache.tmp").write_text("cache", encoding="utf-8")

    observed_internal_flags: dict[str, bool] = {}

    def fake_stage1_review(rows):
        assert {row.ext for row in rows} == {".md", ".tmp"}
        return {".md"}

    def fake_final_review(rows):
        nonlocal observed_internal_flags
        observed_internal_flags = {row.path: row.internal_candidate for row in rows}
        return set()

    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        final_review_fn=fake_final_review,
    )

    assert observed_internal_flags[str(tmp_path / "notes.md")] is True
    assert observed_internal_flags[str(tmp_path / "cache.tmp")] is False
    assert not any("Stage 2: Path Tiering" in line for line in logs)


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
        final_review_fn=lambda rows: {row.path for row in rows[:1]},
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
        final_review_fn=lambda _rows: set(),
    )

    assert not any("using sample data" in line.lower() for line in logs)
    assert any("no files discovered" in line.lower() for line in logs)


def test_run_backup_pipeline_applies_suffix_risk_overrides(tmp_path) -> None:
    (tmp_path / "cache.tmp").write_text("cache", encoding="utf-8")
    observed_rows = []
    observed_ext_batches: list[list[str]] = []

    def fake_stage1_review(rows):
        nonlocal observed_rows
        observed_rows = rows
        return {row.ext for row in rows if row.label == "keep"}

    def fake_suffix_risk(exts: list[str]) -> dict[str, dict[str, object]]:
        observed_ext_batches.append(exts)
        return {
            ".tmp": {
                "risk": "high_value",
                "confidence": 0.95,
                "reason": "Requested by user policy",
            }
        }

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=fake_stage1_review,
        final_review_fn=lambda _rows: set(),
        suffix_risk_fn=fake_suffix_risk,
    )

    assert len(observed_rows) == 1
    assert observed_rows[0].ext == ".tmp"
    assert observed_rows[0].label == "drop"
    assert "hard" in observed_rows[0].reason.lower()
    assert observed_ext_batches == [[]]


def test_run_backup_pipeline_uses_ai_to_choose_non_harddrop_suffixes(tmp_path) -> None:
    (tmp_path / "report.abc").write_text("content", encoding="utf-8")

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
        final_review_fn=lambda _rows: set(),
        suffix_risk_fn=lambda _exts: {
            ".abc": {
                "risk": "low_value",
                "confidence": 0.91,
                "reason": "Model judged non-user artifact",
            }
        },
    )

    assert len(observed_rows) == 1
    assert observed_rows[0].ext == ".abc"
    assert observed_rows[0].label == "drop"
    assert "model judged" in observed_rows[0].reason.lower()


def test_run_backup_pipeline_uses_rule_when_one_suffix_parse_falls_back(
    tmp_path,
) -> None:
    (tmp_path / "note.txt").write_text("content", encoding="utf-8")
    (tmp_path / "junk.apache").write_text("content", encoding="utf-8")

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
        final_review_fn=lambda _rows: set(),
        suffix_risk_fn=lambda _exts: {
            ".txt": {
                "risk": "high_value",
                "confidence": 0.9,
                "reason": "User notes",
            },
            ".apache": {
                "risk": "neutral",
                "confidence": 0.0,
                "reason": "LLM parse fallback",
            },
        },
    )

    by_ext = {row.ext: row for row in observed_rows}
    assert by_ext[".txt"].label == "keep"
    assert by_ext[".apache"].label == "drop"
    assert "likely" in by_ext[".apache"].reason.lower()


def test_run_backup_pipeline_passes_full_paths_to_path_risk_function(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.tmp").write_text("b", encoding="utf-8")
    observed_paths: list[str] = []
    observed_review_rows = []

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

    def fake_final_review(rows):
        nonlocal observed_review_rows
        observed_review_rows = rows
        return set()

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[tmp_path],
        stage1_review_fn=lambda rows: {row.ext for row in rows},
        final_review_fn=fake_final_review,
        path_risk_fn=fake_path_risk,
        send_full_path_to_ai=True,
    )

    assert all(str(tmp_path) in item for item in observed_paths)
    row_by_path = {row.path: row for row in observed_review_rows}
    low_path = str(tmp_path / "b.tmp")
    assert row_by_path[low_path].ai_risk == "low_value"
    assert "Likely temp" in row_by_path[low_path].reason


def test_run_backup_pipeline_shows_stage1_and_stage2_only() -> None:
    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        stage1_review_fn=lambda _rows: {".pdf", ".jpg"},
        final_review_fn=lambda rows: {row.path for row in rows[:1]},
    )

    joined = "\n".join(logs)
    assert "Stage 1: Suffix Screening" in joined
    assert "Stage 2: Final Review and Backup" in joined
    assert "Stage 2: Path Tiering" not in joined
    assert "Stage 3" not in joined


def test_run_backup_pipeline_includes_filtered_and_ignored_files_in_final_review(
    tmp_path,
) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / "keep.md").write_text("keep", encoding="utf-8")
    (src_root / "drop.bin").write_text("drop", encoding="utf-8")
    (src_root / ".venv").mkdir()
    (src_root / ".venv" / "ignored.py").write_text("ignored", encoding="utf-8")

    observed_rows = []

    def fake_final_review(rows):
        nonlocal observed_rows
        observed_rows = rows
        return set()

    run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        source_roots=[src_root],
        stage1_review_fn=lambda _rows: {".md"},
        final_review_fn=fake_final_review,
    )

    observed_paths = {row.path for row in observed_rows}
    assert str(src_root / "keep.md") in observed_paths
    assert str(src_root / "drop.bin") in observed_paths
    assert str(src_root / ".venv" / "ignored.py") in observed_paths
