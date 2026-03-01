# Final Review Stage-2 Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose only Stage 1 and Stage 2 to users, keep internal tiering unchanged, and let final review display/select all files including ignored and Stage1-filtered files.

**Architecture:** Keep internal recommendation flow by splitting pipeline data into an internal tiering view and a final review view. Rename stage3-facing code to final-review naming and rename stage2 builder naming to internal-tiering naming. Merge recommendation metadata onto full-file final review rows so user manual selection can override earlier filters.

**Tech Stack:** Python 3.10+, typer, rich/questionary, pytest

---

### Task 1: Add failing tests for renamed final-review API and user-facing stage labels

**Files:**
- Modify: `tests/pipeline/test_run_backup_pipeline_tui.py`
- Modify: `tests/pipeline/test_run_backup_pipeline_execution.py`
- Create: `tests/tui/test_final_review.py`
- Create: `tests/tui/test_final_review_tree_flow.py`

**Step 1: Write the failing tests**

```python
def test_run_backup_pipeline_logs_stage2_final_review_only() -> None:
    logs = run_backup_pipeline(...)
    assert any("Stage 2: Final Review and Backup" in line for line in logs)
    assert not any("Stage 3" in line for line in logs)
    assert not any("Stage 2: Path Tiering" in line for line in logs)
```

Add imports for `src.tui.final_review` API names instead of `src.tui.stage3_review` names.

**Step 2: Run tests to verify RED**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py tests/tui/test_final_review.py -q`
Expected: FAIL due missing renamed module/functions and old stage labels.

**Step 3: Keep tests focused and minimal**

No implementation yet.

**Step 4: Re-run one failing test to confirm stable RED**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py::test_run_backup_pipeline_logs_stage2_final_review_only -q`
Expected: FAIL

**Step 5: Commit**

```bash
git add tests/pipeline/test_run_backup_pipeline_tui.py tests/pipeline/test_run_backup_pipeline_execution.py tests/tui/test_final_review.py tests/tui/test_final_review_tree_flow.py
git commit -m "test: add failing coverage for final-review stage naming"
```

### Task 2: Refactor stage3 module to final-review naming

**Files:**
- Move: `src/tui/stage3_review.py` -> `src/tui/final_review.py`
- Modify: `src/tui/tree_selection.py`
- Modify: `src/cli.py`
- Modify: `src/pipeline/run_backup.py`
- Modify: tests importing old module paths

**Step 1: Write one failing import test first**

```python
def test_final_review_module_exports_expected_symbols() -> None:
    from src.tui.final_review import FinalReviewRow, run_final_review
```

**Step 2: Run test to verify RED**

Run: `python3 -m pytest tests/tui/test_final_review.py::test_final_review_module_exports_expected_symbols -q`
Expected: FAIL (module/symbol not found).

**Step 3: Write minimal implementation**

- Rename dataclass and functions consistently:
  - `PathReviewRow` -> `FinalReviewRow`
  - `run_stage3_review` -> `run_final_review`
- Update all imports/callers.
- Update tree-selection docstring mentioning stage 3 to final review.

**Step 4: Run focused tests to GREEN**

Run: `python3 -m pytest tests/tui/test_final_review.py tests/tui/test_final_review_tree_flow.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/final_review.py src/tui/tree_selection.py src/cli.py src/pipeline/run_backup.py tests/tui/test_final_review.py tests/tui/test_final_review_tree_flow.py
git commit -m "refactor: rename stage3 review API to final review"
```

### Task 3: Add all-files final review merge behavior with internal-tiering preserved

**Files:**
- Modify: `src/pipeline/run_backup.py`
- Modify: `tests/pipeline/test_run_backup_pipeline_tui.py`
- Modify: `tests/pipeline/test_run_backup_pipeline_execution.py`

**Step 1: Write failing behavior tests**

```python
def test_final_review_receives_all_files_including_ignored_and_stage1_filtered(tmp_path) -> None:
    ...
    assert str(tmp_path / "ignored" / "x.log") in observed_paths
    assert str(tmp_path / "nonwhitelist.bin") in observed_paths


def test_copy_respects_final_selection_for_previously_filtered_files(tmp_path) -> None:
    ...
    assert (target / "src" / "ignored" / "x.log").exists()
```

**Step 2: Run tests to verify RED**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py -k "all_files or filtered" -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- Add full-file collection for final review view.
- Keep existing internal tiering builder behavior for recommendation metadata.
- Add merge builder so final review rows include all files with source markers.
- Rename `_build_stage2_rows` to `_build_internal_tiering_rows`.
- Update copy phase to use final selected paths against full-file index.

**Step 4: Run tests to verify GREEN**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py tests/pipeline/test_run_backup_pipeline_execution.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/pipeline/run_backup.py tests/pipeline/test_run_backup_pipeline_tui.py tests/pipeline/test_run_backup_pipeline_execution.py
git commit -m "feat: allow final review to include all scanned files"
```

### Task 4: Keep AI defaults behavior scoped to internal tiering candidates

**Files:**
- Modify: `src/tui/final_review.py`
- Modify: `tests/tui/test_final_review_tree_flow.py`

**Step 1: Write failing tests**

```python
def test_ai_directory_defaults_do_not_auto_select_non_internal_candidates() -> None:
    ...
```

**Step 2: Run tests to verify RED**

Run: `python3 -m pytest tests/tui/test_final_review_tree_flow.py -k "ai_directory_defaults" -q`
Expected: FAIL

**Step 3: Write minimal implementation**

- Add `internal_candidate: bool` flag on final review rows.
- Apply AI directory default decisions only on `internal_candidate=True` paths.

**Step 4: Run tests to verify GREEN**

Run: `python3 -m pytest tests/tui/test_final_review_tree_flow.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tui/final_review.py tests/tui/test_final_review_tree_flow.py
git commit -m "fix: scope ai directory defaults to internal candidates"
```

### Task 5: Update docs and run final regression

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/architecture.zh-CN.md`

**Step 1: Add failing doc assertions**

```python
def test_readme_mentions_stage2_final_review() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "Stage 2: Final Review and Backup" in content
```

**Step 2: Run test to verify RED**

Run: `python3 -m pytest tests/test_readme_contains_privacy_boundary.py -q`
Expected: FAIL until docs updated.

**Step 3: Update docs**

- Explain user-visible two-stage model.
- Explain final review includes all files and user selection overrides earlier filters.

**Step 4: Run focused + full regression**

Run: `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py tests/pipeline/test_run_backup_pipeline_execution.py tests/tui/test_final_review.py tests/tui/test_final_review_tree_flow.py tests/test_readme_contains_privacy_boundary.py -q`
Expected: PASS

Run: `python3 -m pytest -q`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md README.zh-CN.md docs/architecture.md docs/architecture.zh-CN.md tests/test_readme_contains_privacy_boundary.py
git commit -m "docs: align user-facing stages with final-review flow"
```
