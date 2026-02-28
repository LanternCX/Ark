# Ark Architecture

## Pipeline

Ark uses a staged pipeline:

1. Collector
2. Signals
3. AI Router
4. Decision Engine
5. TUI Review
6. Backup Executor

## Runtime Entry

- CLI root command `ark` opens a top-level TUI menu.
- TUI settings manage runtime config (`target`, `source_roots`, `dry_run`,
  `non_interactive`).
- Config is persisted in a local JSON file and reloaded on next run.
- Pipeline execution remains orchestrated by `ark/pipeline/run_backup.py`.

## Design Principles

- High cohesion and low coupling.
- Minimal hard-coded rules.
- Provider-driven extensibility.
- Human review required before backup execution.
