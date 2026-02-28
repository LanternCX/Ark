# Ark Agent Operating Notes

## Purpose

This file defines repository-specific operating expectations for coding agents.

## Core Rules

1. Keep all production code and comments in English.
2. Maintain bilingual user documentation (`README.md`, `README.zh-CN.md`).
3. Follow Git Flow with `main`, `dev`, and `feat/*` or `feature/*` branches.
4. Do not use git worktree in this repository.
5. Use Angular conventional commit messages.
6. Add co-author trailer when requested:
   `Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>`.

## Technical Constraints

- TUI implementation must use `questionary + rich`.
- LLM routing must use `litellm`.
- Favor modular architecture with low coupling and clear boundaries.

## Local Skill Location

Project-level custom skills are stored under `.opencode/skills`:

- `.opencode/skills/code-standard/SKILL.md`
- `.opencode/skills/doc-maintainer/SKILL.md`
- `.opencode/skills/git-workflow/SKILL.md`
