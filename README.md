# Ark

Ark is an AI-assisted backup agent for system migration and reinstall preparation.

## Quick Start

Run Ark from source without installing to system environment:

```bash
python3 main.py
```

Optional (if installed):

```bash
ark
```

Ark opens a top-level TUI menu:

1. `Settings`
2. `Execute Backup`
3. `Exit`

All runtime options are configured in TUI and persisted locally.

Config file path: `<runtime-root>/.ark/config.json`

`<runtime-root>` means:

- when running source: directory containing `main.py`
- when running packaged binary: directory containing the executable

## Development Docs

- Architecture: `docs/architecture.md`
- Google OAuth setup (Gemini): `docs/google-oauth-setup.md`

## Release Packaging

- GitHub Actions release workflow builds both `windows-x64` and `macos-arm64` artifacts.
- Each artifact bundles runtime-local defaults under the release directory:
  - `.ark/config.json`
  - `src/rules/baseline.ignore`
  - `src/rules/suffix_rules.toml`

## TUI Stage Guide

This section explains each TUI stage in user terms: what it does, what happens if you choose it, and what is recommended.

### Stage 0: Main Menu

1. `Settings`
   - Purpose: configure backup and LiteLLM options.
   - Consequence: values are saved to `<runtime-root>/.ark/config.json` and reused next run.
   - Recommendation: finish settings before first execution.
2. `Execute Backup`
   - Purpose: run the full staged backup flow.
   - Consequence: if `Dry run` is `False`, files are actually copied.
   - Recommendation: run one dry run first.
3. `Exit`
   - Purpose: leave Ark.
   - Consequence: no execution happens.
   - Recommendation: exit only after confirming your latest settings are saved.

### Stage 1: `Settings -> Backup Settings`

- `Backup target path`
  - Purpose: destination root for mirrored files.
  - Consequence: wrong or unwritable path causes backup failure or wrong destination.
  - Recommendation: use a stable writable disk path.
- `Source roots (comma separated)`
  - Purpose: source directories Ark scans and considers for backup.
  - Consequence: missing paths cause data omission; overly broad paths increase noise and risk.
  - Recommendation: start from high-value directories only (for example Documents/Pictures/Projects).
- `Dry run?`
  - Purpose: simulate the full flow without copying.
  - Consequence: no files are written when enabled.
  - Recommendation: keep enabled during first validation.
- `Non-interactive reviews?`
  - Purpose: skip manual review prompts and use defaults.
  - Consequence: faster runs but higher misclassification risk.
  - Recommendation: keep disabled for important migrations.

### Stage 2: `Settings -> LLM Settings`

- `Enable LiteLLM integration?`
  - Purpose: turn AI-assisted decisions on or off.
  - Consequence: when enabled, provider/model configuration is required.
  - Recommendation: enable only after you configure provider and key.
- `LLM provider group`
  - Purpose: choose provider family (OpenAI-compatible, Frontier, China-friendly, Local/Custom).
  - Consequence: controls available platforms and default model presets.
  - Recommendation: choose the group with the best availability and cost for your region.
- `LLM platform`
  - Purpose: choose the exact provider endpoint.
  - Consequence: affects compatibility, latency, and billing.
  - Recommendation: start with a mainstream provider preset, then optimize.
- `Recommended model preset`
  - Purpose: choose one of three top model presets for the selected provider.
  - Consequence: this becomes the default model seed for next step.
  - Recommendation: pick the middle option first if you want balanced cost and quality.
- `Override recommended model?`
  - Purpose: decide whether to use a custom model id.
  - Consequence: when `No`, Ark uses the preset directly and skips custom input.
  - Recommendation: keep `No` unless you need a specific model string.
- `LLM model`
  - Purpose: select model used by LiteLLM calls.
  - Consequence: impacts quality, speed, and token cost.
  - Recommendation: this field appears only when override is enabled; use LiteLLM model ids exactly as documented (including required provider prefixes like `zai/...` or `deepseek/...`).
- `LLM base URL (optional)`
  - Purpose: override endpoint for compatible gateways or local services.
  - Consequence: wrong URL causes connection failures.
  - Recommendation: keep preset/default unless you use custom infrastructure.
- `Gemini authentication method` (Gemini only)
  - Purpose: choose `api_key` or `google_oauth`.
  - Consequence: changes required credential inputs and validation rules.
  - Recommendation: use OAuth for long-running personal workflows; use API key for quick setup.
- `Google client id` / `Google client secret` (Gemini OAuth only)
  - Purpose: configure OAuth client credentials used to mint refresh tokens.
  - Consequence: invalid values block OAuth login and runtime refresh.
  - Recommendation: create Desktop OAuth credentials and keep them local-only.
- `Login with Google in browser now?` (Gemini OAuth only)
  - Purpose: launch browser auth and capture refresh token immediately.
  - Consequence: when skipped, execution will fail until refresh token is provided.
  - Recommendation: run it during settings to avoid runtime blockers.
- `LLM API key`
  - Purpose: authenticate requests to the selected provider.
  - Consequence: invalid key causes auth failures; key is stored in `<runtime-root>/.ark/config.json`.
  - Recommendation: use a dedicated key with appropriate quota limits.
- `Use AI suffix risk classification?`
  - Purpose: allow AI risk labels to influence Stage 1 default suffix selections.
  - Consequence: disabled means suffix defaults rely on local heuristics only.
  - Recommendation: enable unless you need deterministic local-only behavior.
- `Use AI path pruning suggestions?`
  - Purpose: allow AI path-level scoring to influence Stage 2/Stage 3 defaults.
  - Consequence: disabled means no AI path pruning signal is applied.
  - Recommendation: enable for large trees where manual triage is costly.
- `Send full file paths to AI?`
  - Purpose: choose between minimal metadata mode and full-path mode.
  - Consequence: full-path mode improves pruning quality but shares full path strings.
  - Recommendation: enable only when you accept full-path sharing.
- `Hide low-value branches by default?`
  - Purpose: set Stage 3 initial pruning mode (`hide_low_value` or `show_all`).
  - Consequence: affects initial visibility only; you can switch modes during review.
  - Recommendation: enable for faster first-pass decisions.
- `Test LLM connectivity now?`
  - Purpose: send a `hello` probe request with current LLM settings.
  - Consequence: immediately shows whether auth/model/endpoint are reachable and prints model reply.
  - Recommendation: keep enabled after changing provider, model, key, or OAuth settings.

### Stage 3: `Execute Backup`

1. `Stage 1: Suffix Screening`
   - Purpose: first-pass filtering by suffix categories.
   - Consequence: selected suffixes decide which files proceed.
   - Recommendation: be conservative if unsure; avoid filtering too aggressively.
   - UI: suffixes are grouped by category buckets (Document/Image/Code/Archive/Media/Executable/Temp/Cache/Other).
   - AI mode: when LLM is enabled, suffix keep/drop/not_sure defaults are generated by remote LLM classification with local fallback.
   - Local rules mode: scan and category baselines are loaded from rule files (`src/rules/baseline.ignore`, `src/rules/suffix_rules.toml`) instead of hard-coded lists.
2. `Stage 2: Path Tiering`
   - Purpose: combine local signals and AI heuristics into tiers.
   - Consequence: tier outputs shape final candidate priority.
   - Recommendation: pay extra attention to critical personal/work directories.
3. `Stage 3: Final Review and Backup`
   - Purpose: final confirmation and copy execution.
   - Consequence: with `Dry run=False`, this produces real copied files.
   - Recommendation: use tree paging to review folder-level decisions first, then confirm selected count.
   - Controls: `Enter` opens/expands folder, `Space` toggles selection.

### Stage 3 Tree Review

- Final selection uses a paginated tree view instead of a flat one-line path list.
- Folder nodes support tri-state selection:
  - `checked`: all descendant files selected
  - `partial`: only part of descendants selected
  - `unchecked`: no descendants selected
- Toggling a folder applies recursively to all descendants.
- Low-value branches can be hidden by default to reduce noise and can be shown again in the same review session.
- Symbol-first controls use `●`/`◐`/`○` and `▸`/`▾` with rich-colored tree panels.
- Each folder is rendered as one line only (no duplicate open/toggle rows).
- AI DFS mode: when LLM path decision is enabled, Stage 3 runs serial directory DFS decisions (`keep/drop/not_sure`) before interactive review.
- In DFS mode, `drop` recursively unselects the full subtree but traversal still continues for complete-tree analysis.
- After DFS completes, Ark prints an AI summary and then enters one final interactive confirmation pass.

### Resumable Execution

- Backup runs now save checkpoints under `<runtime-root>/.ark/state/backup_runs/`.
- If a matching unfinished run exists, Ark provides a recovery menu:
  - `Resume latest`
  - `Restart new`
  - `Discard and restart`
- Checkpoints include scan progress, AI pruning progress, stage-3 tree selection state, and copy progress.

### Runtime Progress And Logs

- During execution, Ark emits live progress hints such as:
  - current scan root/directory
  - current AI batch processing status
  - current file copy progress
- Runtime logs are written to `<runtime-root>/.ark/logs/ark.log` with rotating log files.
- Per-run structured events are stored as JSONL in `<runtime-root>/.ark/state/backup_runs/<run_id>.events.jsonl`.
- LiteLLM dependency logs are filtered to reduce console noise while keeping actionable warnings.

### Rule Files

- `src/rules/baseline.ignore`: open-source-style gitignore baseline used during scan pruning.
- `src/rules/suffix_rules.toml`: suffix category and hard-drop/keep defaults used by Stage 1 fallback.
- Per-source `.gitignore` and optional `.arkignore` are merged with baseline rules during scan.

### Suggested First-Run Flow

1. Configure `Backup Settings`.
2. Configure `LLM Settings`.
3. Run `Execute Backup` with `Dry run=True`.
4. Review logs and selections.
5. Turn `Dry run` off and run again for real backup.

## Privacy Boundary

Ark supports two AI data-sharing modes:

1. Minimal metadata mode
   - basename
   - extension
   - parent_dir_name (last segment only)
   - size_bucket
   - mtime_bucket
2. Full path mode (opt-in)
   - full file path strings are sent for suffix/path pruning recommendations

Ark sends no file content.

## Technology

- Language: Python
- TUI: questionary + rich
- LLM routing: litellm
- License: MIT

## Git Workflow

- Base branches: `main`, `dev`
- Feature branches: `feat/*` or `feature/*`
- Commit style: Angular conventional commits
- No git worktree usage

## Status

This project is under active development.
