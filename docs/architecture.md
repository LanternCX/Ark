# Ark Architecture (Developer)

This document is developer-facing. For user operation flow, refer to TUI sections in `README.md`.

## 1. Layer Boundaries

Ark enforces one-way dependencies:

`collector/signals/ai -> decision -> tui/backup -> cli`

- `ark/collector/*`: file discovery and metadata extraction.
- `ark/signals/*`: local heuristic scoring.
- `ark/ai/*`: model batching/router/auth integration.
- `ark/decision/*`: tier decision logic.
- `ark/tui/*`: user interaction and review.
- `ark/backup/*`: mirror copy execution.
- `ark/cli.py`: entrypoint wiring only.

## 2. Runtime Flow

1. `ark` enters TUI main menu.
2. User edits settings in `Backup Settings` and `LLM Settings`.
3. Settings persist to `~/.ark/config.json` via `JSONConfigStore`.
4. `Execute Backup` runs staged pipeline in `ark/pipeline/run_backup.py`.
5. Stage 1/2/3 decisions produce final selected paths.
6. Stage 3 uses paginated tree navigation with tri-state folder selection.
7. `backup.executor` mirrors selected files unless dry run.

## 3. Configuration Model

`PipelineConfig` contains two groups:

- Backup execution fields (`target`, `source_roots`, `dry_run`, `non_interactive`).
- LLM fields (`llm_enabled`, provider/model/base URL/auth credentials).

Validation rules run before execution. Typical blockers:

- Missing target/source roots.
- LLM enabled without provider/model.
- Gemini OAuth selected without client id/client secret/refresh token.

## 4. AI Routing Strategy

- Non-Gemini providers default to LiteLLM API key flow.
- Gemini supports:
  - `api_key` mode.
  - `google_oauth` mode with browser login and token refresh.
- OAuth token refresh uses Google official auth SDK.

AI classification scopes:

- Suffix risk recommendation can influence stage-1 default whitelist.
- Path risk recommendation can influence stage-2 reasons and stage-3 low-value pruning defaults.
- Full path payloads are supported when configured; no file content is sent.

## 5. Testing Contract

- Add tests before behavior changes (TDD).
- Keep tests under mirrored `tests/` paths.
- Run focused tests first, then full `pytest`.

## 6. Documentation Contract

- User docs must remain bilingual in README (`README.md`, `README.zh-CN.md`).
- Developer docs in `docs/` should avoid repeating skill governance content.
- OAuth onboarding details live in `docs/google-oauth-setup.md` and `docs/google-oauth-setup.zh-CN.md`.
