# Stage1 + Stage3 AI DFS Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable AI-driven suffix classification in Stage1 and serial DFS directory decisions in Stage3, then present one global summary for final confirmation.

**Architecture:** Keep Ark layer boundaries unchanged and add focused AI decision helpers that feed Stage1 defaults and Stage3 review defaults. Stage3 runs an AI DFS pass over directories first (`keep/drop/not_sure`) while always traversing full tree, then hands final selection to one confirmation review.

**Tech Stack:** Python 3.10+, typer, questionary/prompt_toolkit, rich, litellm, pytest

---

## Execution Tasks

1. Add tests for Stage3 DFS decision semantics (`drop` recursive unselect, full traversal, summary output).
2. Implement Stage3 AI DFS pass and integrate with existing tree review checkpoint flow.
3. Add tests for LLM decision client parsing and fallback behavior.
4. Implement LLM-backed suffix/path/directory decision helpers and wire from CLI when LLM enabled.
5. Update docs for Stage1 AI classification + Stage3 AI DFS summary behavior.
6. Run focused tests and full suite.
