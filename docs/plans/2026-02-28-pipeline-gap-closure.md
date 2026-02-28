# Ark Pipeline Gap Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align the repository with the existing backup-agent plan by replacing sample-only pipeline flow with real source scanning, tiering, and executable mirror copy in `ark backup run`.

**Architecture:** Keep `ark/cli.py` thin and place orchestration in `ark/pipeline/run_backup.py`. Build runtime rows from collector + signals + decision modules, keep TUI review as the human checkpoints, and only execute copy through `ark.backup.executor` after Stage 3 approval. Preserve deterministic behavior for tests via injected review functions.

**Tech Stack:** Python 3.10+, Typer, pathlib, dataclasses, questionary + rich, pytest.

---

### Task 1: Real Source Discovery In Pipeline

**Files:**
- Modify: `ark/pipeline/run_backup.py`
- Test: `tests/pipeline/test_run_backup_pipeline_tui.py`

**Step 1: Write the failing test**

Add a test that passes `source_roots=[tmp_path]` with files like `report.pdf` and `cache.tmp`, then asserts Stage 1 uses discovered suffixes rather than fixed `_sample_*` rows.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py::test_run_backup_pipeline_builds_stage1_rows_from_source_files -v`
Expected: FAIL because `run_backup_pipeline` has no `source_roots` support and still uses sample rows.

**Step 3: Write minimal implementation**

Implement source-root scanning in `run_backup_pipeline`:
- accept `source_roots: list[Path] | None`
- gather files from roots (`rglob("*")` + `is_file()`)
- build Stage 1 suffix rows from discovered suffixes with simple default labeling
- remove sample-row dependency from Stage 1

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py::test_run_backup_pipeline_builds_stage1_rows_from_source_files -v`
Expected: PASS.

### Task 2: Stage 2 Tiering Connected To Signals/Decision

**Files:**
- Modify: `ark/pipeline/run_backup.py`
- Modify: `ark/signals/extractor.py`
- Test: `tests/pipeline/test_run_backup_pipeline_tui.py`

**Step 1: Write the failing test**

Add a test asserting Stage 2 candidate count is derived from whitelisted Stage 1 extensions and that path rows include tiering based on `extension_score` + `classify_tier`.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py::test_run_backup_pipeline_filters_stage2_candidates_by_whitelist -v`
Expected: FAIL because Stage 2 still uses fixed sample rows.

**Step 3: Write minimal implementation**

In `run_backup_pipeline`:
- build Stage 2 candidates from discovered files filtered by Stage 1 whitelist
- compute signal score via `ark.signals.extractor.extension_score`
- compute simple deterministic AI score heuristic
- compute confidence and tier via `ark.decision.tiering.classify_tier`
- pass generated `PathReviewRow` list to Stage 3

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py::test_run_backup_pipeline_filters_stage2_candidates_by_whitelist -v`
Expected: PASS.

### Task 3: Execute Real Mirror Copy When Not Dry-Run

**Files:**
- Modify: `ark/pipeline/run_backup.py`
- Modify: `ark/cli.py`
- Test: `tests/pipeline/test_run_backup_pipeline_execution.py` (create)
- Test: `tests/e2e/test_backup_run_happy_path.py`

**Step 1: Write the failing test**

Create a test that:
- builds a temp source tree with at least one selected file
- runs `run_backup_pipeline(..., dry_run=False, source_roots=[src_root], stage*_review_fn=...)`
- asserts copied file exists under `target/<src_root.name>/...`

Also add/adjust CLI smoke test to pass `--source` and keep `--non-interactive`.

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_execution.py::test_run_backup_pipeline_executes_mirror_copy_for_selected_paths -v`
Run: `python3 -m pytest tests/e2e/test_backup_run_happy_path.py::test_backup_run_command_smoke -v`
Expected: first FAIL due no copy execution path; second may fail until CLI wiring includes `--source`.

**Step 3: Write minimal implementation**

Implement copy execution path:
- map selected Stage 3 path strings back to `(src_root, src_path)`
- call `ark.backup.executor.mirror_copy_one` for each selected file when `dry_run=False`
- log copy counts
- wire CLI `--source` option to pass `source_roots` into pipeline

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_execution.py::test_run_backup_pipeline_executes_mirror_copy_for_selected_paths -v`
Run: `python3 -m pytest tests/e2e/test_backup_run_happy_path.py::test_backup_run_command_smoke -v`
Expected: PASS.

### Task 4: Verify End-To-End Regression Safety

**Files:**
- No code changes required unless tests fail

**Step 1: Run focused suite**

Run: `python3 -m pytest tests/pipeline -q`

**Step 2: Run full suite**

Run: `python3 -m pytest -q`

**Step 3: Update README status only if behavior wording is now inaccurate**

If needed, adjust `README.md` and `README.zh-CN.md` to remove statements that imply sample-only execution.
