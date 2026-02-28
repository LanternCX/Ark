# Ark TUI-First Entry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `ark` the one-command entrypoint where all runtime backup configuration is done in TUI and persisted across runs.

**Architecture:** Add a unified pipeline config model plus JSON config store, then route root CLI to a top-level TUI main menu (`Settings / Execute Backup / Exit`). Keep `ark/cli.py` thin and keep pipeline execution logic in `ark/pipeline/run_backup.py`.

**Tech Stack:** Python 3.10+, typer, questionary, rich, pytest

---

### Task 1: Add failing CLI root behavior test

**Files:**
- Modify: `tests/test_cli_smoke.py`

**Step 1: Write the failing test**

```python
def test_cli_root_runs_without_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli_smoke.py::test_cli_root_runs_without_subcommand -v`

Expected: FAIL because root command does not yet implement the new behavior.

**Step 3: Write minimal implementation**

- Adjust `ark/cli.py` to provide root callback/command behavior.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli_smoke.py::test_cli_root_runs_without_subcommand -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli_smoke.py ark/cli.py
git commit -m "feat: add root ark command entry"
```

### Task 2: Add config model and JSON persistence

**Files:**
- Create: `ark/pipeline/config.py`
- Create: `ark/state/config_store.py`
- Modify: `ark/state/__init__.py`
- Test: `tests/state/test_config_store_contract.py`

**Step 1: Write the failing test**

```python
def test_pipeline_config_roundtrip(tmp_path) -> None:
    store = JSONConfigStore(tmp_path / "config.json")
    store.save(PipelineConfig(target="X:/ArkBackup", source_roots=["."], dry_run=True, non_interactive=False))
    loaded = store.load()
    assert loaded.target == "X:/ArkBackup"
    assert loaded.source_roots == ["."]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/state/test_config_store_contract.py::test_pipeline_config_roundtrip -v`

Expected: FAIL because `PipelineConfig`/`JSONConfigStore` do not yet exist.

**Step 3: Write minimal implementation**

- Implement dataclass for `PipelineConfig`.
- Implement load/save store with safe defaults when file does not exist.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/state/test_config_store_contract.py::test_pipeline_config_roundtrip -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add ark/pipeline/config.py ark/state/config_store.py ark/state/__init__.py tests/state/test_config_store_contract.py
git commit -m "feat: add persistent pipeline config store"
```

### Task 3: Add TUI main menu orchestration

**Files:**
- Create: `ark/tui/main_menu.py`
- Test: `tests/tui/test_main_menu.py`

**Step 1: Write the failing test**

```python
def test_main_menu_can_edit_and_execute() -> None:
    # inject fake prompt functions and assert execution callback receives edited config
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/tui/test_main_menu.py -v`

Expected: FAIL because menu orchestration does not yet exist.

**Step 3: Write minimal implementation**

- Add loop with top-level choices: settings/execute/exit.
- Add editable fields for target/source roots/dry run/non-interactive.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/tui/test_main_menu.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add ark/tui/main_menu.py tests/tui/test_main_menu.py
git commit -m "feat: add main menu for tui-first flow"
```

### Task 4: Wire CLI root to menu and pipeline

**Files:**
- Modify: `ark/cli.py`
- Modify: `ark/pipeline/run_backup.py`
- Modify: `tests/e2e/test_backup_run_happy_path.py`

**Step 1: Write the failing test**

```python
def test_ark_root_smoke_runs_staged_output() -> None:
    # invoke app with [] and assert stage lines are visible using non-interactive stubs
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/e2e/test_backup_run_happy_path.py -v`

Expected: FAIL until root command wiring is complete.

**Step 3: Write minimal implementation**

- Root command loads persisted config.
- Root command invokes main menu orchestration.
- Execute action calls `run_backup_pipeline` with config values.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/e2e/test_backup_run_happy_path.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add ark/cli.py ark/pipeline/run_backup.py tests/e2e/test_backup_run_happy_path.py
git commit -m "feat: route root ark command through tui pipeline"
```

### Task 5: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`

**Step 1: Update docs**

- Replace usage examples to `ark` root command.
- Explain that runtime options now come from TUI settings.

**Step 2: Run full tests**

Run: `python3 -m pytest -q`

Expected: PASS.

**Step 3: Commit**

```bash
git add README.md README.zh-CN.md docs/architecture.md
git commit -m "docs: describe tui-first ark entry flow"
```
