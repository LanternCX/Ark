# Ark Agent Guide

## Purpose
This file defines repository-specific operating rules for coding agents working in Ark.
Prefer existing project patterns over invention.

## Project Snapshot
- Language: Python (`>=3.10`)
- CLI framework: `typer`
- TUI stack: `questionary + rich`
- LLM routing layer: `litellm`
- Data contracts: `pydantic` and `dataclasses`
- Testing: `pytest`
- Build backend: `setuptools`

## Sources Of Truth
- `README.md`
- `README.zh-CN.md`
- `docs/architecture.md`
- `docs/architecture.zh-CN.md`
- `docs/google-oauth-setup.md`
- `docs/google-oauth-setup.zh-CN.md`
- `docs/privacy-boundary.md`
- `.opencode/skills/code-standard/SKILL.md`
- `.opencode/skills/doc-maintainer/SKILL.md`
- `.opencode/skills/git-workflow/SKILL.md`

## External Rule Files (Cursor/Copilot)
Checked locations in this repository:
- `.cursor/rules/`: not present
- `.cursorrules`: not present
- `.github/copilot-instructions.md`: not present

If these files are added later, treat them as mandatory constraints.

## Environment Setup
Use Python 3.10+ and install package + dev dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

## Build, Lint, Test Commands

### Core Verification
```bash
python3 -m pytest -q
make test
make verify
```

### Single-Test Workflows (important)
- Single file:

```bash
python3 -m pytest tests/test_cli_smoke.py -q
```

- Single test function (preferred when making focused changes):

```bash
python3 -m pytest tests/test_cli_smoke.py::test_cli_help_contains_backup_group -v
```

- By keyword:

```bash
python3 -m pytest -k "tiering" -q
```

- Extra debug detail:

```bash
python3 -m pytest tests/path/to/test_file.py::test_name -vv
```

### Lint/Format Status
- No dedicated lint/format command is currently configured.
- Do not assume `ruff`, `black`, `isort`, or `mypy` are available.
- Passing tests is the required quality gate today.

## Architecture Boundaries
Maintain one-way dependency flow:

`collector/signals/ai -> decision -> tui/backup -> cli`

Rules:
- Avoid cross-layer shortcuts.
- Keep modules cohesive and single-purpose.
- Pass dependencies explicitly; avoid hidden global state.
- Keep core logic deterministic unless I/O is required.

## Code Style Guidelines

### Imports
- Use absolute imports rooted at `ark`.
- Group imports: standard library, third-party, local package.
- Prefer explicit imports; avoid wildcard imports.
- Avoid import-time side effects.

### Formatting
- Follow existing style: 4-space indentation and readable line breaks.
- Keep functions focused and reasonably small.
- Keep docstrings concise and purposeful.
- Add comments only for non-obvious logic.
- Keep production code and comments in English.

### Types And Contracts
- Add explicit type hints for parameters and return values.
- Prefer modern concrete annotations (`list[str]`, `dict[str, str]`, `set[str]`).
- Use `pydantic` or `dataclass` at boundaries.
- Keep validation/coercion close to input boundaries.

### Naming Conventions
- Files/modules: `snake_case.py`
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Tests: `test_<behavior>` with behavior-focused assertions

### Error Handling
- Raise precise exceptions with actionable messages.
- Prefer `ValueError` for invalid values and `KeyError` for missing keyed entities.
- Validate early and fail fast on unsupported states.
- Never silently swallow exceptions.

### CLI/TUI Conventions
- Keep `ark/cli.py` thin (argument parsing and command wiring only).
- Place orchestration in pipeline modules such as `ark/pipeline/run_backup.py`.
- Keep TUI behavior and prompts in `ark/tui/*` using `questionary + rich`.

## Testing Expectations
- Prefer TDD for features and bug fixes.
- Mirror source layout under `tests/`.
- Cover happy paths and relevant edge/failure paths.
- Add targeted regression tests for fixed bugs.
- Run the smallest relevant tests first, then run full tests for substantial changes.

## Documentation Expectations
- If behavior changes, update both `README.md` and `README.zh-CN.md`.
- Keep architecture and privacy docs aligned with implementation.
- Do not document features as complete before tests pass.

## Git Workflow Expectations
- Branches: `main`, `dev`, and `feat/*` or `feature/*`.
- Commit style: Angular conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Do not use git worktrees in this repository.
- Keep commits scoped, reviewable, and validated by tests.

## Agent Checklist Before Finishing
1. Changes follow architecture boundaries and style rules.
2. At least one relevant targeted test was run.
3. Full test suite was run when the change is substantial.
4. User-facing docs were updated when workflows/behavior changed.
5. No conflict with project governance or `.opencode/skills` rules.
