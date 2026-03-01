# Runtime rules.md Context Injection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Inject optional runtime `rules.md` text into backup-time AI prompts so users can tune keep/drop preferences without changing source code.

**Architecture:** Keep orchestration in `src/cli.py`: load `<runtime-root>/rules.md` once per run, then pass it through LLM kwargs. Keep AI prompt logic centralized in `src/ai/decision_client.py` with one shared prompt composer and bounded rules-context normalization. Preserve all existing fallbacks (dry-run local-only behavior, parse fallback behavior, and local heuristic paths).

**Tech Stack:** Python 3.10+, dataclasses, typer, litellm router, pytest

---

### Task 1: Add runtime path helper for `rules.md`

**Files:**
- Modify: `src/runtime_paths.py`
- Modify: `tests/test_runtime_paths.py`
- Test: `tests/test_runtime_paths.py`

**Step 1: Write the failing test**

```python
def test_runtime_rules_md_path_uses_runtime_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))
    assert runtime_paths.get_runtime_rules_md_path() == tmp_path / "rules.md"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_runtime_paths.py::test_runtime_rules_md_path_uses_runtime_root -v`
Expected: FAIL because `get_runtime_rules_md_path` does not exist yet.

**Step 3: Write minimal implementation**

```python
def get_runtime_rules_md_path() -> Path:
    """Return runtime-local optional AI preference rules path."""
    return get_runtime_root() / "rules.md"
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_runtime_paths.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_runtime_paths.py src/runtime_paths.py
git commit -m "feat: add runtime rules markdown path helper"
```

### Task 2: Load runtime rules text in CLI and propagate via LLM kwargs

**Files:**
- Modify: `src/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Test: `tests/test_cli_smoke.py`

**Step 1: Write the failing tests**

```python
def test_execute_backup_forwards_runtime_rules_context_to_llm(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))
    (tmp_path / "rules.md").write_text("Prefer keep documents", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_llm_suffix_risk(_exts, **kwargs):
        captured.update(kwargs)
        return {".pdf": {"risk": "high_value", "confidence": 1.0, "reason": "ai"}}

    # monkeypatch BackupRunStore + run_backup_pipeline and trigger suffix_risk_fn
    ...
    assert captured["rules_context"] == "Prefer keep documents"


def test_execute_backup_missing_runtime_rules_md_uses_empty_context(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))
    # no rules.md
    ...
    assert captured["rules_context"] == ""
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_cli_smoke.py -k "rules_context" -q`
Expected: FAIL because CLI does not read/forward `rules.md` yet.

**Step 3: Write minimal implementation**

```python
from src.runtime_paths import get_runtime_rules_md_path


def _load_runtime_rules_context() -> str:
    path = get_runtime_rules_md_path()
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to read runtime rules.md: %s", exc)
        return ""


def _llm_call_kwargs(config: PipelineConfig, rules_context: str = "") -> dict[str, str]:
    return {
        ...,
        "rules_context": rules_context,
    }
```

Then call `_load_runtime_rules_context()` once in `_execute_backup` and pass it to `_llm_call_kwargs`.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cli_smoke.py -k "rules_context or dry_run_uses_local_heuristics" -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_smoke.py src/cli.py
git commit -m "feat: load runtime rules context for llm dispatch"
```

### Task 3: Add shared decision-client prompt composer with bounded rules injection

**Files:**
- Modify: `src/ai/decision_client.py`
- Modify: `tests/ai/test_decision_client.py`
- Test: `tests/ai/test_decision_client.py`

**Step 1: Write the failing tests**

```python
def test_llm_path_risk_includes_rules_block_when_rules_context_present(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_classify_batch(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return '{"items":[]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)
    decision_client.llm_path_risk(["/a/b.txt"], model="openai/gpt-4.1-mini", rules_context="Prefer docs")

    assert "rules.md" in captured["prompt"]
    assert "Prefer docs" in captured["prompt"]


def test_llm_path_risk_omits_rules_block_when_rules_context_empty(monkeypatch) -> None:
    ...
    assert "rules.md" not in captured["prompt"]


def test_rules_context_is_truncated_with_marker(monkeypatch) -> None:
    ...
    assert "...[truncated]" in captured["prompt"]
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/ai/test_decision_client.py -q`
Expected: FAIL because rules-context prompt composition is not implemented.

**Step 3: Write minimal implementation**

```python
MAX_RULES_CONTEXT_CHARS = 12000


def _normalize_rules_context(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""
    if len(normalized) <= MAX_RULES_CONTEXT_CHARS:
        return normalized
    return f"{normalized[:MAX_RULES_CONTEXT_CHARS].rstrip()}\n...[truncated]"


def _compose_prompt(base_block: str, input_block: str, rules_context: str) -> str:
    rules = _normalize_rules_context(rules_context)
    if not rules:
        return f"{base_block} {input_block}"
    return (
        f"{base_block} {input_block}\n\n"
        "Preference rules from runtime rules.md (hints only; do not change schema):\n"
        f"{rules}"
    )
```

Update all three public functions (`llm_suffix_risk`, `llm_path_risk`, `llm_directory_decision`) to accept `rules_context: str = ""` and build prompts via `_compose_prompt`.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/ai/test_decision_client.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/ai/test_decision_client.py src/ai/decision_client.py
git commit -m "feat: inject runtime rules into ai decision prompts"
```

### Task 4: Update user/dev/privacy docs for `rules.md` behavior

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/architecture.zh-CN.md`
- Modify: `docs/privacy-boundary.md`
- Test: `tests/test_readme_contains_privacy_boundary.py`

**Step 1: Write/update doc assertions where needed**

```python
def test_readme_mentions_runtime_rules_md_path() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "<runtime-root>/rules.md" in content
```

**Step 2: Run doc test to verify it fails**

Run: `python3 -m pytest tests/test_readme_contains_privacy_boundary.py -q`
Expected: FAIL until docs are updated.

**Step 3: Write minimal documentation updates**
- README EN/ZH: add runtime `rules.md` location and effect scope.
- Architecture EN/ZH: add rules-context injection flow (`cli -> ai decision prompts`).
- Privacy boundary: state that optional `rules.md` text is sent only when remote LLM path is active.

**Step 4: Run docs test to verify it passes**

Run: `python3 -m pytest tests/test_readme_contains_privacy_boundary.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md README.zh-CN.md docs/architecture.md docs/architecture.zh-CN.md docs/privacy-boundary.md tests/test_readme_contains_privacy_boundary.py
git commit -m "docs: describe runtime rules context and privacy scope"
```

### Task 5: Regression verification and integration commit

**Files:**
- Modify: none (verification-only unless regressions are found)
- Test: `tests/test_runtime_paths.py`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/ai/test_decision_client.py`
- Test: `tests/test_readme_contains_privacy_boundary.py`

**Step 1: Run focused regression set**

Run: `python3 -m pytest tests/test_runtime_paths.py tests/test_cli_smoke.py tests/ai/test_decision_client.py tests/test_readme_contains_privacy_boundary.py -q`
Expected: PASS

**Step 2: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS

**Step 3: Final integration commit (if working tree still has staged changes)**

```bash
git add -A
git commit -m "feat: support runtime rules.md preferences in ai backup decisions"
```

**Step 4: Capture verification evidence for PR**

Run: `git status && git log --oneline -n 5`
Expected: clean working tree and clear commit trail.
