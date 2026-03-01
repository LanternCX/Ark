# Runtime-Local Entry And Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable source execution via `main.py`, store runtime data under `<runtime-root>/.ark`, and add macOS release packaging alongside Windows.

**Architecture:** Introduce a central runtime path resolver and route all persisted state/log paths through it. Keep CLI wiring thin, keep pipeline behavior unchanged, and only update persistence and packaging integration points.

**Tech Stack:** Python 3.10+, typer, rich, questionary, pytest, GitHub Actions, PyInstaller

---

### Task 1: Add runtime path resolver

**Files:**
- Create: `src/runtime_paths.py`
- Create: `tests/test_runtime_paths.py`

**Step 1: Write the failing test**

```python
def test_runtime_data_dir_uses_script_directory_when_argv_points_to_main(monkeypatch, tmp_path):
    script = tmp_path / "main.py"
    script.write_text("print('x')\n", encoding="utf-8")
    monkeypatch.setenv("ARK_RUNTIME_ROOT", "")
    monkeypatch.setattr("sys.argv", [str(script)])
    assert get_runtime_data_dir() == tmp_path / ".ark"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_runtime_paths.py -q`
Expected: FAIL because module/functions do not exist yet.

**Step 3: Write minimal implementation**

```python
def get_runtime_root() -> Path: ...
def get_runtime_data_dir() -> Path: ...
def get_runtime_config_path() -> Path: ...
def get_runtime_logs_dir() -> Path: ...
def get_runtime_backup_runs_dir() -> Path: ...
def get_runtime_rules_dir() -> Path: ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_runtime_paths.py -q`
Expected: PASS

### Task 2: Route config/log/state/rules to runtime-local paths

**Files:**
- Modify: `src/cli.py`
- Modify: `src/runtime_logging.py`
- Modify: `src/rules/local_rules.py`
- Modify: `tests/test_runtime_logging.py`
- Modify: `tests/test_cli_smoke.py`

**Step 1: Write failing tests**
- Assert CLI uses runtime-local config/run-state paths.
- Assert runtime logging writes to runtime-local log file.

**Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_cli_smoke.py tests/test_runtime_logging.py -q`
Expected: FAIL on old `Path.home()` assertions/behavior.

**Step 3: Write minimal implementation**
- Replace `Path.home() / ".ark"/...` usage in CLI and logging.
- Resolve baseline/suffix rule files using runtime rules directory first, package fallback second.

**Step 4: Re-run tests**

Run: `python3 -m pytest tests/test_cli_smoke.py tests/test_runtime_logging.py tests/rules/test_local_rules.py -q`
Expected: PASS

### Task 3: Add top-level main entry and macOS packaging

**Files:**
- Create: `main.py`
- Modify: `.github/workflows/package.yml`
- Modify: `tests/test_package_workflow_exists.py`

**Step 1: Write failing tests**
- Assert workflow defines macOS build in matrix.
- Assert workflow bundles runtime config + rules files.

**Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_package_workflow_exists.py -q`
Expected: FAIL because workflow currently only builds Windows and no runtime rules bundling.

**Step 3: Write minimal implementation**
- Add `main.py` calling `ark.cli.main()`.
- Switch workflow to matrix build for Windows + macOS.
- Bundle `.ark/config.json` and `src/rules/*` into release zip.

**Step 4: Re-run tests**

Run: `python3 -m pytest tests/test_package_workflow_exists.py -q`
Expected: PASS

### Task 4: Update bilingual docs and run regressions

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/architecture.zh-CN.md`
- Modify: `docs/privacy-boundary.md`
- Modify: `docs/google-oauth-setup.md`
- Modify: `docs/google-oauth-setup.zh-CN.md`

**Step 1: Update docs**
- Replace `~/.ark` references with runtime-local `<runtime-root>/.ark` descriptions.
- Add source-run command with `python3 main.py`.
- Document Windows + macOS packaging behavior.

**Step 2: Run focused regressions**

Run: `python3 -m pytest tests/test_runtime_paths.py tests/test_cli_smoke.py tests/test_runtime_logging.py tests/test_package_workflow_exists.py -q`
Expected: PASS

**Step 3: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS
