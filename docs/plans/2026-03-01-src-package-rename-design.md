# Src Package Rename Design

## Goal

Align repository naming by renaming the current package directory from `src/` to `src/` while keeping `python3 main.py` as the primary local run command.

## Decisions

1. Rename package root directory `src/` to `src/`.
2. Rename all Python imports from `ark.*` to `src.*`.
3. Keep runtime folder name `.ark` unchanged for now to avoid changing on-disk user data contract.
4. Keep root entry script `main.py` and update it to import `src.cli`.
5. Keep CLI command name `ark` in packaging metadata, but point script entry to `src.cli:main`.

## Scope

- Python package tree rename (`src/` -> `src/`).
- Import path updates in production code and tests.
- Workflow and packaging path updates (`src/rules/*` -> `src/rules/*`).
- Documentation updates where code paths reference `src/*` internals.

## Non-goals

- Changing persisted runtime folder `.ark` naming.
- Changing external CLI command from `ark` to another name.
- Any behavior changes in backup pipeline logic.

## Risks And Mitigation

- Risk: missed imports after rename.
  - Mitigation: global import replacement + full test suite.
- Risk: workflow bundles wrong rule paths.
  - Mitigation: update release workflow assertions and run workflow tests.
- Risk: docs drift after package rename.
  - Mitigation: update EN/ZH README and architecture docs in the same change.

## Validation

1. `python3 -m pytest tests/test_package_workflow_exists.py -q`
2. `python3 -m pytest -q`
