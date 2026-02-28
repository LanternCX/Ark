# Ark

Ark is an AI-assisted backup agent for system migration and reinstall preparation.

## Core Workflow

1. Stage 1: suffix screening with AI suggestions and manual TUI review.
2. Stage 2: path tiering using local signals plus AI semantics.
3. Stage 3: final TUI review and mirror backup execution.

## Privacy Boundary

Ark sends only minimal metadata to AI:
- basename
- extension
- parent_dir_name (last segment only)
- size_bucket
- mtime_bucket

Ark sends no file content.

## Technology

- Language: Python
- TUI: questionary + rich
- LLM routing: litellm
- License: MIT

## Git Workflow

- Base branches: `main`, `dev`
- Feature branches: `feat/*` or `feature/*`
- Commit style: Angular conventional commits
- No git worktree usage

## Status

This project is under active development.
