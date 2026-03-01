# Ark Architecture (Developer)

This document is developer-facing. For user operation flow, refer to TUI sections in `README.md`.

## 1. Layer Boundaries

Ark enforces one-way dependencies:

`collector/signals/ai -> decision -> tui/backup -> cli`

- `src/collector/*`: file discovery and metadata extraction.
- `src/signals/*`: local heuristic scoring.
- `src/ai/*`: model batching/router/auth integration.
- `src/decision/*`: tier decision logic.
- `src/tui/*`: user interaction and review.
- `src/backup/*`: mirror copy execution.
- `main.py`: source-run entrypoint.
- `src/cli.py`: Typer app wiring and runtime orchestration entry.

## 2. Runtime Flow

1. `python3 main.py` (or packaged binary / installed `ark`) enters TUI main menu.
2. User edits settings in `Backup Settings` and `LLM Settings`.
3. Settings persist to `<runtime-root>/.ark/config.json` via `JSONConfigStore`.
4. `Execute Backup` runs staged pipeline in `src/pipeline/run_backup.py`.
5. Stage 1 groups suffixes by category buckets for layered decisions.
6. Stage 1/2/3 decisions produce final selected paths.
7. Stage 3 uses paginated tree navigation with tri-state folder selection and symbol-first UI controls.
8. `backup.executor` mirrors selected files unless dry run.
9. Runtime checkpoints persist resumable progress under `<runtime-root>/.ark/state/backup_runs`.

`<runtime-root>` means the directory containing `main.py` (source mode) or the packaged executable (binary mode).

## 3. Configuration Model

`PipelineConfig` contains three groups:

- Backup execution fields (`target`, `source_roots`, `dry_run`, `non_interactive`).
- LLM routing fields (`llm_enabled`, `llm_provider_group`, `llm_provider`, `llm_model`, `llm_base_url`, `llm_api_key`, `llm_auth_method`, `google_client_id`, `google_client_secret`, `google_refresh_token`).
- AI decision fields (`ai_suffix_enabled`, `ai_path_enabled`, `send_full_path_to_ai`, `ai_prune_mode`).

Validation rules run before execution. Typical blockers:

- Missing target/source roots.
- LLM enabled without provider/model.
- Gemini OAuth selected without client id/client secret/refresh token.
- Invalid prune mode outside `hide_low_value` / `show_all`.

## 4. AI Routing Strategy

- Non-Gemini providers default to LiteLLM API key flow.
- Gemini supports:
  - `api_key` mode.
  - `google_oauth` mode with browser login and token refresh.
- OAuth token refresh uses Google official auth SDK.

AI classification scopes:

- Suffix risk recommendation can influence stage-1 default whitelist.
- Path risk recommendation can influence stage-2 reasons and stage-3 low-value pruning defaults.
- Stage-3 can run serial AI directory DFS decisions (`keep/drop/not_sure`) before final interactive confirmation.
- Full path payloads are supported when configured; no file content is sent.
- Scan pruning and suffix category defaults are loaded from external rule files, then fused with AI decisions.

## 5. Runtime Checkpoint And Logging

- Pipeline supports resumable runs with stage checkpoints (`scan`, `stage1`, `stage2`, `review`, `copy`).
- Interruptions can be resumed using persisted run metadata and checkpoint payloads.
- Runtime logging uses rich console output + rotating file logs.
- LiteLLM dependency loggers are aligned and filtered to warning-level noise floor.
- Per-run structured events are appended to JSONL for operational replay.

## 6. Testing Contract

- Add tests before behavior changes (TDD).
- Keep tests under mirrored `tests/` paths.
- Run focused tests first, then full `pytest`.

## 7. Documentation Contract

- User docs must remain bilingual in README (`README.md`, `README.zh-CN.md`).
- Developer docs in `docs/` should avoid repeating skill governance content.
- OAuth onboarding details live in `docs/google-oauth-setup.md` and `docs/google-oauth-setup.zh-CN.md`.
