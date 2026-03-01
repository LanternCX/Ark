# LLM Probe, Logging Filter, And Stage3 Single-Line Nodes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update LLM settings probe to send hello and print model response, filter LiteLLM logs effectively, and make Stage3 folder nodes single-line with enter-expand and space-toggle semantics.

**Architecture:** Keep existing Ark pipeline boundaries unchanged. Apply focused changes in `src/ai/router.py`, `src/runtime_logging.py`, `src/tui/main_menu.py`, and `src/tui/stage3_review.py` with tests first for each behavior. Reuse current tree state/checkpoint logic and only adjust interaction rendering and prompt plumbing.

**Tech Stack:** Python 3.10+, typer, questionary, rich, litellm, pytest

---

### Task 1: LLM probe message and output text

**Files:**
- Modify: `tests/tui/test_main_menu.py`
- Modify: `src/ai/router.py`
- Modify: `src/tui/main_menu.py`

**Step 1: Write failing tests**
- Add assertions that connectivity check sends `hello` semantics and success output includes model reply message.

**Step 2: Run failing tests**
- Run: `python3 -m pytest tests/tui/test_main_menu.py::test_main_menu_can_run_llm_connectivity_check -q`

**Step 3: Minimal implementation**
- Update `check_llm_connectivity` to send hello and return concise reply text.
- Update settings success output to print returned message.

**Step 4: Re-run tests**
- Same command, expect PASS.

### Task 2: LiteLLM logging filter alignment

**Files:**
- Modify: `tests/test_runtime_logging.py`
- Modify: `src/runtime_logging.py`

**Step 1: Write failing tests**
- Assert dependency logger align helpers exist and apply target levels to `LiteLLM` and child loggers.

**Step 2: Run failing tests**
- Run: `python3 -m pytest tests/test_runtime_logging.py -q`

**Step 3: Minimal implementation**
- Add `adopt_dependency_logger(s)` helpers.
- Apply to `("LiteLLM",)` in `setup_runtime_logging`.

**Step 4: Re-run tests**
- Same command, expect PASS.

### Task 3: Stage3 single-line folder node interaction

**Files:**
- Modify: `tests/tui/test_stage3_tree_flow.py`
- Modify: `src/tui/stage3_review.py`

**Step 1: Write failing tests**
- Assert one folder row per directory in choices.
- Assert no separate open/toggle folder duplicate lines.

**Step 2: Run failing tests**
- Run: `python3 -m pytest tests/tui/test_stage3_tree_flow.py -q`

**Step 3: Minimal implementation**
- Build single node line values.
- Wire node action parsing to distinguish enter-expand vs space-toggle semantics through prompt adapter.

**Step 4: Re-run tests**
- Same command, expect PASS.

### Task 4: Regression and docs

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Steps:**
- Update interaction notes for Stage3 single-line folder nodes and controls.
- Run targeted regressions then full suite:
  - `python3 -m pytest tests/tui/test_main_menu.py tests/test_runtime_logging.py tests/tui/test_stage3_review.py tests/tui/test_stage3_tree_flow.py -q`
  - `python3 -m pytest -q`
