# Ark Backup Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `ark`, a Windows-first, cross-platform-architecture CLI/TUI backup agent that performs AI-assisted two-stage filtering and safe mirror backup with two mandatory human review checkpoints.

**Architecture:** Use a modular pipeline with strict boundaries: collector -> signals -> AI router -> decision engine -> review TUI -> backup executor. Keep rules minimal and provider-driven to avoid rule sprawl. Default to local SQLite state (no deployment needed), with optional JSON backend.

**Tech Stack:** Python 3.12+, Typer, questionary, rich, LiteLLM, pydantic, pytest, pytest-mock, pathlib, concurrent.futures, sqlite3.

---

### Task 1: Repository Bootstrap And Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `ark/__init__.py`
- Create: `ark/cli.py`
- Create: `tests/test_cli_smoke.py`

**Step 1: Write the failing test**

```python
# tests/test_cli_smoke.py
from typer.testing import CliRunner
from ark.cli import app

def test_cli_help_contains_backup_group():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "backup" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_smoke.py::test_cli_help_contains_backup_group -v`
Expected: FAIL with import/module error because `ark.cli` and app are not implemented.

**Step 3: Write minimal implementation**

```python
# ark/cli.py
import typer

app = typer.Typer(help="Ark backup agent")
backup_app = typer.Typer(help="Backup commands")
app.add_typer(backup_app, name="backup")

@backup_app.command("run")
def run_backup(target: str):
    raise typer.Exit(code=0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_smoke.py::test_cli_help_contains_backup_group -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml README.md README.zh-CN.md LICENSE .gitignore ark/__init__.py ark/cli.py tests/test_cli_smoke.py
git commit -m "feat: bootstrap ark project with CLI entrypoint"
```

### Task 2: Domain Models And State Backend (SQLite + JSON)

**Files:**
- Create: `ark/models.py`
- Create: `ark/state/base.py`
- Create: `ark/state/sqlite_store.py`
- Create: `ark/state/json_store.py`
- Create: `tests/state/test_state_store_contract.py`

**Step 1: Write the failing test**

```python
# tests/state/test_state_store_contract.py
from ark.state.sqlite_store import SQLiteStateStore

def test_sqlite_store_can_create_and_load_session(tmp_path):
    db = tmp_path / "state.db"
    store = SQLiteStateStore(db)
    session_id = store.create_session("windows")
    loaded = store.get_session(session_id)
    assert loaded.platform == "windows"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/state/test_state_store_contract.py::test_sqlite_store_can_create_and_load_session -v`
Expected: FAIL because state classes do not exist.

**Step 3: Write minimal implementation**

```python
# ark/models.py
from pydantic import BaseModel

class Session(BaseModel):
    session_id: str
    platform: str
```

```python
# ark/state/sqlite_store.py
import sqlite3
import uuid
from pathlib import Path
from ark.models import Session

class SQLiteStateStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, platform TEXT)")
        conn.commit()
        conn.close()

    def create_session(self, platform: str) -> str:
        sid = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO sessions (id, platform) VALUES (?, ?)", (sid, platform))
        conn.commit()
        conn.close()
        return sid

    def get_session(self, session_id: str) -> Session:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT id, platform FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()
        return Session(session_id=row[0], platform=row[1])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/state/test_state_store_contract.py::test_sqlite_store_can_create_and_load_session -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/models.py ark/state/base.py ark/state/sqlite_store.py ark/state/json_store.py tests/state/test_state_store_contract.py
git commit -m "feat: add pluggable state backend with sqlite default"
```

### Task 3: Collector Layer (Windows First, Cross-Platform Interface)

**Files:**
- Create: `ark/platforms/base.py`
- Create: `ark/platforms/windows.py`
- Create: `ark/collector/scanner.py`
- Create: `tests/collector/test_suffix_scan.py`

**Step 1: Write the failing test**

```python
# tests/collector/test_suffix_scan.py
from ark.collector.scanner import collect_suffix_summary

def test_collect_suffix_summary_deduplicates_extensions(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c").write_text("c")
    summary = collect_suffix_summary([tmp_path])
    assert ".txt" in summary.extensions
    assert "c" in summary.no_extension_names
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_suffix_scan.py::test_collect_suffix_summary_deduplicates_extensions -v`
Expected: FAIL because scanner is missing.

**Step 3: Write minimal implementation**

```python
# ark/collector/scanner.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SuffixSummary:
    extensions: set[str]
    no_extension_names: set[str]

def collect_suffix_summary(roots: list[Path]) -> SuffixSummary:
    exts, noext = set(), set()
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file():
                if p.suffix:
                    exts.add(p.suffix.lower())
                else:
                    noext.add(p.name)
    return SuffixSummary(exts, noext)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/collector/test_suffix_scan.py::test_collect_suffix_summary_deduplicates_extensions -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/platforms/base.py ark/platforms/windows.py ark/collector/scanner.py tests/collector/test_suffix_scan.py
git commit -m "feat: implement suffix scanning collector with platform abstraction"
```

### Task 4: LiteLLM Batch Classifier With Strict Minimal Metadata

**Files:**
- Create: `ark/ai/schemas.py`
- Create: `ark/ai/router.py`
- Create: `ark/ai/batcher.py`
- Create: `tests/ai/test_batcher_contract.py`

**Step 1: Write the failing test**

```python
# tests/ai/test_batcher_contract.py
from ark.ai.batcher import chunk_records

def test_chunk_records_respects_batch_size():
    records = list(range(250))
    chunks = list(chunk_records(records, batch_size=100))
    assert [len(c) for c in chunks] == [100, 100, 50]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ai/test_batcher_contract.py::test_chunk_records_respects_batch_size -v`
Expected: FAIL because batcher module does not exist.

**Step 3: Write minimal implementation**

```python
# ark/ai/batcher.py
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

def chunk_records(records: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    bucket: list[T] = []
    for r in records:
        bucket.append(r)
        if len(bucket) >= batch_size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/ai/test_batcher_contract.py::test_chunk_records_respects_batch_size -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/ai/schemas.py ark/ai/router.py ark/ai/batcher.py tests/ai/test_batcher_contract.py
git commit -m "feat: add litellm batch pipeline primitives"
```

### Task 5: Stage 1 TUI Review (Suffix Allowlist)

**Files:**
- Create: `ark/tui/stage1_review.py`
- Modify: `ark/cli.py`
- Create: `tests/tui/test_stage1_review_defaults.py`

**Step 1: Write the failing test**

```python
# tests/tui/test_stage1_review_defaults.py
from ark.tui.stage1_review import apply_default_selection

def test_apply_default_selection_keeps_high_confidence_keep_labels():
    rows = [{"ext": ".pdf", "label": "keep", "confidence": 0.95}]
    selected = apply_default_selection(rows, threshold=0.8)
    assert ".pdf" in selected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tui/test_stage1_review_defaults.py::test_apply_default_selection_keeps_high_confidence_keep_labels -v`
Expected: FAIL because stage1 review logic is missing.

**Step 3: Write minimal implementation**

```python
# ark/tui/stage1_review.py
def apply_default_selection(rows: list[dict], threshold: float) -> set[str]:
    picked = set()
    for row in rows:
        if row["label"] == "keep" and row["confidence"] >= threshold:
            picked.add(row["ext"])
    return picked
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tui/test_stage1_review_defaults.py::test_apply_default_selection_keeps_high_confidence_keep_labels -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/tui/stage1_review.py ark/cli.py tests/tui/test_stage1_review_defaults.py
git commit -m "feat: add stage1 tui defaults for suffix review"
```

### Task 6: Stage 2 Path Tiering (Signals + AI Fusion)

**Files:**
- Create: `ark/signals/extractor.py`
- Create: `ark/decision/tiering.py`
- Create: `ark/providers/feedback.py`
- Create: `tests/decision/test_tiering.py`

**Step 1: Write the failing test**

```python
# tests/decision/test_tiering.py
from ark.decision.tiering import classify_tier

def test_classify_tier_routes_low_confidence_to_tier2():
    tier = classify_tier(signal_score=0.9, ai_score=0.2, confidence=0.4)
    assert tier == "tier2"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/decision/test_tiering.py::test_classify_tier_routes_low_confidence_to_tier2 -v`
Expected: FAIL because tiering engine does not exist.

**Step 3: Write minimal implementation**

```python
# ark/decision/tiering.py
def classify_tier(signal_score: float, ai_score: float, confidence: float) -> str:
    if confidence < 0.6:
        return "tier2"
    total = (signal_score + ai_score) / 2
    if total >= 0.75:
        return "tier1"
    if total >= 0.4:
        return "tier2"
    return "tier3"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/decision/test_tiering.py::test_classify_tier_routes_low_confidence_to_tier2 -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/signals/extractor.py ark/decision/tiering.py ark/providers/feedback.py tests/decision/test_tiering.py
git commit -m "feat: implement tier decision fusion with confidence guardrails"
```

### Task 7: Stage 3 Final Review And Mirror Backup Executor

**Files:**
- Create: `ark/tui/stage3_review.py`
- Create: `ark/backup/executor.py`
- Create: `ark/backup/manifest.py`
- Create: `tests/backup/test_mirror_copy.py`

**Step 1: Write the failing test**

```python
# tests/backup/test_mirror_copy.py
from ark.backup.executor import mirror_copy_one

def test_mirror_copy_one_recreates_relative_path(tmp_path):
    src_root = tmp_path / "C"
    src_root.mkdir()
    src = src_root / "Users" / "me" / "doc.txt"
    src.parent.mkdir(parents=True)
    src.write_text("hello")

    dst_root = tmp_path / "backup"
    mirror_copy_one(src_root, src, dst_root)
    assert (dst_root / "C" / "Users" / "me" / "doc.txt").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/backup/test_mirror_copy.py::test_mirror_copy_one_recreates_relative_path -v`
Expected: FAIL because backup executor is missing.

**Step 3: Write minimal implementation**

```python
# ark/backup/executor.py
import shutil
from pathlib import Path

def mirror_copy_one(src_root: Path, src_path: Path, dst_root: Path) -> None:
    rel = src_path.relative_to(src_root)
    dst = dst_root / src_root.name / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/backup/test_mirror_copy.py::test_mirror_copy_one_recreates_relative_path -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/tui/stage3_review.py ark/backup/executor.py ark/backup/manifest.py tests/backup/test_mirror_copy.py
git commit -m "feat: add mirror backup executor with source-root replication"
```

### Task 8: End-To-End Command Wiring (`ark backup run`)

**Files:**
- Create: `ark/pipeline/run_backup.py`
- Modify: `ark/cli.py`
- Create: `tests/e2e/test_backup_run_happy_path.py`

**Step 1: Write the failing test**

```python
# tests/e2e/test_backup_run_happy_path.py
from typer.testing import CliRunner
from ark.cli import app

def test_backup_run_command_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["backup", "run", "--target", "X:/ArkBackup", "--dry-run"])
    assert result.exit_code == 0
    assert "Stage 1" in result.stdout
    assert "Stage 2" in result.stdout
    assert "Stage 3" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/e2e/test_backup_run_happy_path.py::test_backup_run_command_smoke -v`
Expected: FAIL because run pipeline is not integrated.

**Step 3: Write minimal implementation**

```python
# ark/pipeline/run_backup.py
def run_backup_pipeline(target: str, dry_run: bool) -> list[str]:
    return ["Stage 1", "Stage 2", "Stage 3", f"target={target}", f"dry_run={dry_run}"]
```

```python
# in ark/cli.py command
for line in run_backup_pipeline(target=target, dry_run=dry_run):
    print(line)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/e2e/test_backup_run_happy_path.py::test_backup_run_command_smoke -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add ark/pipeline/run_backup.py ark/cli.py tests/e2e/test_backup_run_happy_path.py
git commit -m "feat: wire end-to-end backup run command"
```

### Task 9: Documentation, Privacy Contract, And Contribution Flow

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Create: `docs/architecture.md`
- Create: `docs/privacy-boundary.md`
- Create: `docs/git-flow.md`

**Step 1: Write the failing test**

```python
# tests/test_readme_contains_privacy_boundary.py
from pathlib import Path

def test_readme_mentions_minimal_metadata_boundary():
    content = Path("README.md").read_text(encoding="utf-8")
    assert "basename" in content
    assert "parent_dir_name" in content
    assert "no file content" in content.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme_contains_privacy_boundary.py::test_readme_mentions_minimal_metadata_boundary -v`
Expected: FAIL because docs are incomplete.

**Step 3: Write minimal implementation**

```markdown
## Privacy Boundary

Ark sends only minimal metadata to AI:
- basename
- extension
- parent_dir_name (last segment only)
- size_bucket
- mtime_bucket

Ark never uploads file content.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme_contains_privacy_boundary.py::test_readme_mentions_minimal_metadata_boundary -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md README.zh-CN.md docs/architecture.md docs/privacy-boundary.md docs/git-flow.md tests/test_readme_contains_privacy_boundary.py
git commit -m "docs: add bilingual docs architecture and privacy contract"
```

### Task 10: Verification Gate

**Files:**
- Create: `Makefile`
- Create: `scripts/verify.sh`

**Step 1: Write the failing test**

```python
# tests/test_verify_script_exists.py
from pathlib import Path

def test_verify_script_exists_and_is_executable():
    script = Path("scripts/verify.sh")
    assert script.exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify_script_exists.py::test_verify_script_exists_and_is_executable -v`
Expected: FAIL because verification script is missing.

**Step 3: Write minimal implementation**

```bash
#!/usr/bin/env bash
set -euo pipefail
pytest -q
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_verify_script_exists.py::test_verify_script_exists_and_is_executable -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add Makefile scripts/verify.sh tests/test_verify_script_exists.py
git commit -m "chore: add verification entrypoint"
```

## Branching And Delivery Sequence (Git Flow)

1. Initialize repository and create `main` + `dev`.
2. Start feature branch from `dev`: `feat/ark-backup-v1`.
3. Execute tasks in order with frequent Angular commits.
4. Merge feature branch -> `dev` after verification.
5. Stabilize and merge `dev` -> `main` for release.

## Validation Checklist Before Merge

- `pytest -q` passes.
- `ark backup run --target <path> --dry-run` works.
- Stage 1 and Stage 3 TUI review screens render.
- AI payload logging confirms minimal metadata boundary.
- Mirror copy reproduces source root structure.
- English + Chinese docs and MIT license are complete.
