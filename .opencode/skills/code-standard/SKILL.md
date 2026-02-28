---
name: code-standard
description: Use when adding or modifying Python source code in this repository and coding conventions or module boundaries need to be enforced.
---

# Code Standard

## Overview
This skill defines coding standards for Ark Python implementation work.
Core principle: keep modules cohesive, interfaces explicit, and side effects isolated.

## Rules
- Write all production code and comments in English.
- Prefer small modules with single responsibilities.
- Keep dependency flow one-way: `collector/signals/ai -> decision -> tui/backup -> cli`.
- Avoid hidden globals; pass dependencies explicitly.
- Use pydantic/dataclasses for structured data contracts.
- Keep functions deterministic unless I/O is required.

## Testing Contract
- Follow TDD for new behavior and bug fixes.
- Add behavior-focused tests under `tests/` matching module layout.
- Validate regression cases for safety-sensitive logic.

## Quick Review Checklist
- Does this change increase coupling across layers?
- Are model contracts typed and validated?
- Are edge cases and failures tested?
- Is naming explicit and consistent?
