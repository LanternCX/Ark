# Ark Architecture

## Pipeline

Ark uses a staged pipeline:

1. Collector
2. Signals
3. AI Router
4. Decision Engine
5. TUI Review
6. Backup Executor

## Design Principles

- High cohesion and low coupling.
- Minimal hard-coded rules.
- Provider-driven extensibility.
- Human review required before backup execution.
