---
name: doc-maintainer
description: Use when updating repository documentation so English and Chinese docs, architecture notes, and privacy boundaries remain consistent.
---

# Doc Maintainer

## Overview
This skill keeps Ark documentation complete and synchronized across languages.
Core principle: every meaningful behavior change must be reflected in user-facing and maintainer-facing docs.

## Required Documents
- `README.md` for English overview and usage.
- `README.zh-CN.md` for Chinese overview and usage.
- `docs/architecture.md` for pipeline/module architecture.
- `docs/privacy-boundary.md` for AI data sharing contract.
- `docs/git-flow.md` for branch and commit workflow.

## Update Rules
- Update both English and Chinese READMEs in the same change when behavior changes.
- Keep privacy claims strict and verifiable in code paths.
- Do not document features as complete before tests pass.
- Keep examples runnable and aligned with current CLI flags.

## Release Note Rules
- Summarize why the change exists, not only what changed.
- Link to changed files and test evidence in PR descriptions.
