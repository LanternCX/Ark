# Ark

Ark is an AI-assisted backup agent for system migration and reinstall preparation.

## Quick Start

Run Ark with a single command:

```bash
ark
```

Ark opens a top-level TUI menu:

1. `Settings`
2. `Execute Backup`
3. `Exit`

All runtime options are configured in TUI and persisted locally.

Config file path: `~/.ark/config.json`

## Development Docs

- Architecture: `docs/architecture.md`
- Google OAuth setup (Gemini): `docs/google-oauth-setup.md`

## TUI Stage Guide

This section explains each TUI stage in user terms: what it does, what happens if you choose it, and what is recommended.

### Stage 0: Main Menu

1. `Settings`
   - Purpose: configure backup and LiteLLM options.
   - Consequence: values are saved to `~/.ark/config.json` and reused next run.
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
- `LLM API key`
  - Purpose: authenticate requests to the selected provider.
  - Consequence: invalid key causes auth failures; key is stored in `~/.ark/config.json`.
  - Recommendation: use a dedicated key with appropriate quota limits.
- `Test LLM connectivity now?`
  - Purpose: send a minimal probe request with current LLM settings.
  - Consequence: immediately shows whether auth/model/endpoint are reachable.
  - Recommendation: keep enabled after changing provider, model, key, or OAuth settings.

### Stage 3: `Execute Backup`

1. `Stage 1: Suffix Screening`
   - Purpose: first-pass filtering by file suffix.
   - Consequence: selected suffixes decide which files proceed.
   - Recommendation: be conservative if unsure; avoid filtering too aggressively.
2. `Stage 2: Path Tiering`
   - Purpose: combine local signals and AI heuristics into tiers.
   - Consequence: tier outputs shape final candidate priority.
   - Recommendation: pay extra attention to critical personal/work directories.
3. `Stage 3: Final Review and Backup`
   - Purpose: final confirmation and copy execution.
   - Consequence: with `Dry run=False`, this produces real copied files.
   - Recommendation: use tree paging to review folder-level decisions first, then confirm selected count.

### Stage 3 Tree Review (New)

- Final selection uses a paginated tree view instead of a flat one-line path list.
- Folder nodes support tri-state selection:
  - `checked`: all descendant files selected
  - `partial`: only part of descendants selected
  - `unchecked`: no descendants selected
- Toggling a folder applies recursively to all descendants.
- Low-value branches can be hidden by default to reduce noise and can be shown again in the same review session.

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
