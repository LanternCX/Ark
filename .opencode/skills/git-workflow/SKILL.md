---
name: git-workflow
description: Use when performing branch, merge, and commit operations in this repository under Git Flow and Angular commit constraints.
---

# Git Workflow

## Overview
This skill enforces Ark repository git workflow requirements.
Core principle: integrate through `dev`, release through `main`, and keep history auditable.

## Branch Model
- Long-lived branches: `main`, `dev`.
- Feature branches: `feat/*` or `feature/*`, branched from `dev`.
- No git worktree usage in this repository.

## Commit Convention
- Use Angular conventional commit style: `feat:`, `fix:`, `docs:`, `chore:`, etc.
- Include co-author trailer when requested:
  `Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>`.

## Merge Policy
- Run tests before merge.
- Merge feature branches into `dev` first.
- Merge `dev` into `main` only after verification gates pass.

## Safety Rules
- Do not use destructive git commands without explicit approval.
- Do not force-push protected branches.
- Keep commits scoped and reviewable.
