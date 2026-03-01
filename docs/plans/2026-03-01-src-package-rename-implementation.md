# Src Package Rename Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the Python package directory from `src/` to `src/` while preserving `python3 main.py` startup and keeping all tests green.

**Architecture:** Keep behavior unchanged and perform a mechanical package-namespace migration. Move package files to `src/`, update all import statements and metadata references, then update docs and CI bundle paths. Validate with focused tests followed by full test suite.

**Tech Stack:** Python 3.10+, typer, rich, questionary, pytest, GitHub Actions, PyInstaller

---

### Task 1: Add failing path-level tests for renamed package references

**Files:**
- Modify: `tests/test_package_workflow_exists.py`
- Test: `tests/test_package_workflow_exists.py`

**Step 1: Write the failing test**

```python
def test_package_workflow_bundles_src_rules_files() -> None:
    content = Path(".github/workflows/package.yml").read_text(encoding="utf-8")
    assert "src/rules/baseline.ignore" in content
    assert "src/rules/suffix_rules.toml" in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_package_workflow_exists.py::test_package_workflow_bundles_src_rules_files -v`
Expected: FAIL because workflow still references `src/rules/*`.

**Step 3: Write minimal implementation**

```yaml
cp "src/rules/baseline.ignore" "bundle/$BUNDLE/src/rules/"
cp "src/rules/suffix_rules.toml" "bundle/$BUNDLE/src/rules/"
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_package_workflow_exists.py -q`
Expected: PASS

### Task 2: Rename package folder and update imports

**Files:**
- Move: `src/` -> `src/`
- Modify: `main.py`
- Modify: `pyproject.toml`
- Modify: `tests/**/*.py` (all `ark.*` imports to `src.*`)
- Modify: `src/**/*.py` (all internal `ark.*` imports to `src.*`)

**Step 1: Write the failing test**

```python
def test_source_entry_imports_src_cli() -> None:
    content = Path("main.py").read_text(encoding="utf-8")
    assert "from src.cli import main" in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_package_workflow_exists.py::test_main_entrypoint_exists -v`
Expected: FAIL after package move until imports/entry are updated.

**Step 3: Write minimal implementation**

```python
# main.py
from src.cli import main
```

```toml
[project.scripts]
ark = "src.cli:main"
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli_smoke.py tests/test_runtime_paths.py -q`
Expected: PASS

### Task 3: Update runtime rules path logic and workflow bundle tree

**Files:**
- Modify: `src/runtime_paths.py`
- Modify: `.github/workflows/package.yml`
- Modify: `tests/test_runtime_paths.py`
- Modify: `tests/test_package_workflow_exists.py`

**Step 1: Write the failing test**

```python
def test_runtime_rules_dir_points_to_src(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))
    assert runtime_paths.get_runtime_rules_dir() == tmp_path / "src" / "rules"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_runtime_paths.py::test_runtime_rules_dir_points_to_src -v`
Expected: FAIL while logic still points to `src/rules`.

**Step 3: Write minimal implementation**

```python
def get_runtime_rules_dir() -> Path:
    return get_runtime_root() / "src" / "rules"
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_runtime_paths.py tests/test_package_workflow_exists.py -q`
Expected: PASS

### Task 4: Update docs and run full regression

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/architecture.zh-CN.md`

**Step 1: Update package path references**

```markdown
- `src/collector/*`
- `src/pipeline/run_backup.py`
- `src/rules/suffix_rules.toml`
```

**Step 2: Run focused tests**

Run: `python3 -m pytest tests/test_package_workflow_exists.py tests/test_runtime_paths.py tests/test_cli_smoke.py -q`
Expected: PASS

**Step 3: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS
