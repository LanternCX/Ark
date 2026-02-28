# Ark TUI-First Entry Design

## Context

The current CLI requires `ark backup run` plus command-line options such as
`--target`, `--source`, `--dry-run`, and `--non-interactive`.

The requested behavior is:

- `ark` should be the direct entry command.
- All existing configuration capabilities should be handled inside TUI.
- Top-level menu should be `Settings / Execute Backup / Exit`.
- Configuration should persist across runs.

## Goals

1. Replace parameter-driven execution flow with a TUI-first flow.
2. Keep existing backup pipeline behavior intact.
3. Keep CLI thin and maintain architecture boundaries.
4. Provide a safe, validated execution path from TUI.

## Non-Goals

- Multi-profile config management.
- Advanced provider tuning pages.
- New backup stages or AI policy changes.

## Proposed Architecture

### 1) Unified config contract

Introduce a `PipelineConfig` contract containing current runtime options:

- `target: str`
- `source_roots: list[str]`
- `dry_run: bool`
- `non_interactive: bool`

This contract is shared between TUI orchestration and pipeline invocation.

### 2) Persistent config store

Introduce a JSON-backed config store for user configuration persistence.

- Load config on startup.
- Save config after each settings mutation.
- Use default config when no file exists.

### 3) Main menu orchestration in TUI

Add a top-level TUI menu with three fixed actions:

1. `Settings`
2. `Execute Backup`
3. `Exit`

`Settings` edits all currently supported runtime values.

`Execute Backup` validates required fields then runs pipeline.

### 4) CLI entry simplification

`ark` root command becomes the main entrypoint and directly opens TUI flow.

The previous parameterized `backup run` flow is removed from user-facing path.

### 5) Pipeline boundary

`ark/pipeline/run_backup.py` remains execution orchestration.

It should consume explicit config-derived values and should not own menu logic.

## Data Flow

1. User runs `ark`.
2. CLI loads persisted config from store.
3. TUI main menu opens.
4. User edits settings (persisted immediately).
5. User selects execute.
6. Validation checks required config.
7. Pipeline runs and logs are shown.
8. Control returns to top-level menu.

## Validation and Error Handling

- Execution guardrails:
  - `target` must be non-empty.
  - `source_roots` must contain at least one valid path string.
- Validation failures are shown in TUI and return to `Settings`/menu.
- Runtime execution exceptions are surfaced as readable lines and do not crash the
  menu loop.

## Testing Strategy

1. CLI tests verify `ark` root execution path.
2. TUI tests verify menu behavior, setting mutation, and persist/load cycle.
3. Pipeline tests continue validating stage flow and copy behavior.
4. E2E smoke test validates one-command entry and staged output.

## Documentation Impact

Update docs to reflect TUI-first usage:

- `README.md`
- `README.zh-CN.md`
- `docs/architecture.md`

## Risks and Mitigations

- Risk: regression in existing `backup run` tests.
  - Mitigation: migrate tests to root command semantics while preserving pipeline
    assertions.
- Risk: config file incompatibility.
  - Mitigation: strict defaults and defensive load behavior.
