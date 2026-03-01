# Runtime rules.md Context Injection Design

## Goal

Allow backup-time AI decisions to consume optional user rules from `<runtime-root>/rules.md` so users can steer suffix/path/directory preferences without changing code.

## Decisions

1. Read only one file: `<runtime-root>/rules.md`.
2. Missing `rules.md` is a normal case and must not block backup.
3. Inject rules only into remote LLM paths (suffix risk, path risk, directory decision).
4. Keep dry-run behavior unchanged: no remote LLM dispatch in dry-run mode.
5. Use one shared prompt composer in `src/ai/decision_client.py` so all LLM decision calls apply the same injection policy.

## Scope

- Add runtime rules context loading in CLI orchestration.
- Pass rules context through LLM call kwargs.
- Add shared prompt composition + truncation behavior in decision client.
- Add targeted tests for prompt injection and runtime loading behavior.
- Update user/developer docs to mention `rules.md` support and boundaries.

## Non-goals

- No changes to local heuristic logic.
- No new UI setting for rules file path.
- No multi-file merge logic (for example per-source rules files).

## Architecture Changes

### 1) Runtime rules context loading (CLI)

In `src/cli.py`, load `<runtime-root>/rules.md` once at backup start.

- Add helper to resolve and read runtime rules text.
- If file does not exist, return empty string.
- If read fails (permissions/encoding/io), degrade to empty string and continue.

### 2) LLM kwargs propagation

Extend `_llm_call_kwargs` payload with `rules_context` and pass through existing dispatches:

- `llm_suffix_risk(..., rules_context=...)`
- `llm_path_risk(..., rules_context=...)`
- `llm_directory_decision(..., rules_context=...)`

This keeps dependency direction intact (`cli -> ai`) and avoids hidden global state.

### 3) Shared prompt composition in decision client

In `src/ai/decision_client.py`, add a shared prompt builder used by all three LLM call sites:

- Base instruction block (strict JSON schema requirement).
- Input payload block (suffixes/paths/directory data).
- Optional rules block when `rules_context` is non-empty.

Rules block contract:

- Explain that rules express preference hints only.
- Explicitly state output schema must not change.
- Preserve existing JSON-only response contract.

## Rules Text Normalization

Normalize `rules_context` before injection:

- Normalize line endings (`\r\n` -> `\n`).
- Trim leading/trailing whitespace.
- Cap max length with a fixed constant (for example 12,000 chars).
- If truncated, append clear marker (`...[truncated]`).

This controls token cost and avoids oversized prompts while keeping behavior deterministic.

## Error Handling

- `rules.md` missing: silent fallback to empty rules context.
- `rules.md` read error: fallback to empty rules context, continue pipeline.
- Parse failures in LLM responses: keep existing fallback behavior unchanged.

## Data Flow

1. `_execute_backup` starts.
2. CLI reads `<runtime-root>/rules.md` into `rules_context`.
3. `rules_context` is added into shared LLM kwargs.
4. Decision client composes prompt via shared builder.
5. Router sends prompt to provider.
6. Existing JSON parsing + fallback logic applies.

## Testing Strategy

1. `tests/ai/test_decision_client.py`
   - prompt includes rules block when `rules_context` is provided.
   - prompt omits rules block when `rules_context` is empty.
   - oversized rules text is truncated with marker.
2. `tests/test_cli_smoke.py`
   - `_execute_backup` reads runtime `rules.md` and forwards value to LLM calls.
   - missing runtime `rules.md` does not fail execution.
   - dry-run still avoids remote LLM dispatch.

Run focused tests first, then full suite when implementation is complete.

## Documentation Scope

Update these files when implementation lands:

- `README.md`
- `README.zh-CN.md`
- `docs/architecture.md`
- `docs/architecture.zh-CN.md`

Document runtime path (`<runtime-root>/rules.md`), effect scope (AI preference only), and privacy boundary impact (still no file content upload).

## Risks And Mitigations

- Risk: verbose user rules may dilute base schema instructions.
  - Mitigation: prepend strict schema guard text and use bounded context length.
- Risk: runtime read failure causes unexpected interruption.
  - Mitigation: never hard-fail on rules read; always degrade to empty rules.
- Risk: inconsistent behavior across suffix/path/directory prompts.
  - Mitigation: single shared prompt composer.
