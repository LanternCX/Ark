# Tree Paging And AI Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add paginated tree-based final selection with folder tri-state behavior, and add AI-driven suffix/path recommendation controls including optional full-path payloads.

**Architecture:** Keep pipeline boundaries unchanged (`collector/signals/ai -> decision -> tui/backup -> cli`). Add pure tree-selection state helpers in `src/tui/tree_selection.py`, keep `src/tui/stage3_review.py` as interaction layer, and extend pipeline orchestration with injectable recommendation functions.

**Tech Stack:** Python 3.10+, typer, questionary, rich, litellm, pytest

---

## Implemented Tasks

1. Added tree-selection state machine and paging helpers.
2. Reworked stage-3 review to support tree navigation, recursive folder toggles, and low-value branch visibility toggling.
3. Extended pipeline config/state persistence with AI recommendation controls.
4. Extended pipeline orchestration to accept suffix/path recommendation functions and optional full-path payload mode.
5. Wired CLI execution path to pass recommendation flags and pruning mode.
6. Added/updated tests for tree flow, pipeline recommendation fusion, config persistence, and CLI wiring.
7. Updated README (EN/ZH) and privacy/architecture docs to reflect tree review and full-path mode.

## Validation

- `python3 -m pytest tests/tui/test_tree_selection.py -q`
- `python3 -m pytest tests/tui/test_stage3_tree_flow.py -q`
- `python3 -m pytest tests/pipeline/test_run_backup_pipeline_tui.py -q`
- `python3 -m pytest tests/tui/test_main_menu.py -q`
- `python3 -m pytest -q`
