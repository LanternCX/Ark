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
6. Internal tiering computes recommendation metadata after Stage 1 and is not shown as a user stage.
7. Stage 2 (final review) uses paginated tree navigation with tri-state folder selection and symbol-first UI controls.
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
- Path risk recommendation can influence internal-tiering reasons and stage-2 low-value pruning defaults.
- Stage-2 can run serial AI directory DFS decisions (`keep/drop/not_sure`) before final interactive confirmation.
- During `dry_run`, AI dispatch uses local heuristics only and skips remote provider calls.
- Optional `<runtime-root>/rules.md` is explicit user-provided preference text and may be included in remote AI prompts for suffix/path/directory hints when remote calls are active.
- `rules.md` hint usage does not change the output JSON schema contract.
- Full path payloads are supported when configured; "no file content" means scanned source files being backed up.
- Scan pruning and suffix category defaults are loaded from external rule files, then fused with AI decisions.
- Final review includes all scanned files, including files filtered by Stage 1 and files matched by ignore rules.
- Internal tiering is not shown as a user stage.

## 5. Runtime Checkpoint And Logging

- Pipeline supports resumable runs with stage checkpoints (`scan`, `stage1`, `internal_tiering`, `final_review`, `copy`).
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
