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
- Keep user docs onboarding-first: explain how to start, configure, run, and recover.
- Avoid maintainer-facing wording in user docs (for example implementation comparisons like "X instead of Y" unless users must make that choice).
- Remove low-level internal details from README-level docs unless they directly affect user actions.
- When updating Settings-related docs, `README.zh-CN.md` MUST include Chinese translation for every user-facing configuration label shown in the UI.
- For Settings walkthroughs, document options in workflow order and explain each option's behavior and user-visible consequence.

## Release Note Rules
- Summarize why the change exists, not only what changed.
- Link to changed files and test evidence in PR descriptions.
