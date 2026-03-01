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

## Guided Setup Flow

The easiest way to use Ark is to make decisions in order: configure backup paths, optionally configure AI, run one dry run, then run the real copy.

### Runtime Framework

Every Ark run follows the same end-to-end flow:

1. **Start and load config**: Ark reads `<runtime-root>/.ark/config.json` and restores your last saved settings.
2. **Main menu decision**: choose `Settings` to adjust behavior or `Execute Backup` to run immediately.
3. **Settings become active**: once saved, updated settings are used by the current run.
4. **Pre-run validation**: before execution, Ark checks required inputs for your chosen mode (paths, source roots, model/auth data when applicable).
5. **Two user-visible execution stages**: Stage 1 (suffix screening) and Stage 2 (final review). Internal tiering still runs, but is not shown as a user stage.
6. **Write behavior**: with `Dry run = No`, files confirmed in Stage 2 are copied; with `Dry run = Yes`, Ark simulates and reports results without file writes, and AI decisions use local heuristics only (no remote LLM requests).
7. **Resume support**: checkpoints are written continuously so interrupted runs can be resumed.

In short: **configure -> preview -> commit**.

### Step 1: `Settings -> Backup Settings`

| Option | What this controls | Behavior and consequence |
| --- | --- | --- |
| `Backup target path` | Destination root for copied files | If this path is wrong or not writable, backup cannot complete as expected. |
| `Source roots (comma separated)` | Which folders Ark scans | Narrow scope can miss files; overly broad scope increases review noise and time. |
| `Dry run?` | Whether Ark actually copies files | `Yes`: full review flow, no file writes, and no remote LLM calls (local heuristics only). `No`: confirmed selections are copied. |
| `Non-interactive reviews?` | Whether manual confirmation screens are shown | `Yes`: faster run with defaults only. `No`: you confirm selections interactively. |

Decision tip: on first use, keep `Dry run? = Yes` and `Non-interactive reviews? = No`.

### Step 2: `Settings -> LLM Settings` (optional)

If LiteLLM is disabled, Ark uses local rules and local heuristics only.

| Option | What this controls | Behavior and consequence |
| --- | --- | --- |
| `Enable LiteLLM integration?` | Enable AI-assisted decisions | `No`: local-only decisions. `Yes`: provider/model/auth settings become active. |
| `LLM provider group` | Provider family | Changes available platform presets and model choices. |
| `LLM platform` | Concrete provider endpoint | Affects compatibility, speed, and billing behavior. |
| `Recommended model preset` | Suggested model shortcut | Pre-fills a practical model choice for the selected platform. |
| `Override recommended model?` | Keep preset or set your own model id | `No`: use preset directly. `Yes`: you must provide an explicit model id. |
| `LLM model (custom allowed)` | Final model id used for requests | Wrong value can cause request errors or unexpected routing. |
| `LLM base URL (optional)` | Custom compatible endpoint | Use only when you rely on a proxy/gateway/local endpoint. |
| `Gemini authentication method` | Gemini auth mode (`api_key` or `google_oauth`) | Controls which Gemini credentials are required. |
| `Google client id` | Gemini OAuth app id | Required for Gemini OAuth login and refresh flow. |
| `Google client secret` | Gemini OAuth app secret | Required for Gemini OAuth login and refresh flow. |
| `Login with Google in browser now?` | Immediate Gemini OAuth login | Writes refresh token now so execution is not blocked later. |
| `LLM API key` | Provider credential | Invalid key causes auth failures; value is stored in local runtime config. |
| `Use AI suffix risk classification?` | AI defaults in Stage 1 | `No`: suffix defaults rely on local logic only. |
| `Use AI path pruning suggestions?` | AI influence in path selection | `No`: path pruning uses local logic only. |
| `Send full file paths to AI?` | Data-sharing scope for AI prompts | `No`: minimal metadata mode. `Yes`: includes full path strings. |
| `Hide low-value branches by default?` | Initial Stage 2 visibility | `Yes`: starts with low-value branches hidden. |
| `Test LLM connectivity now?` | Live probe with current settings | Sends a test request and prints immediate success/failure feedback. |

### Step 3: `Execute Backup`

- `Stage 1: Suffix Screening` builds the first candidate set by file suffix and rule files.
- Internal tiering still computes recommendation metadata, but is not shown as a user stage.
- `Stage 2: Final Review and Backup` includes all scanned files, including files filtered by Stage 1 and files matched by ignore rules.
- In Stage 2, you can manually select any displayed file for backup.

In Stage 2, use `Enter` to expand folders and `Space` to toggle selection.

### Where each setting takes effect

- `Backup target path`, `Source roots`, and `Dry run?` directly change the outcome of `Execute Backup`.
- `Non-interactive reviews?` controls whether manual confirmation screens are shown.
- LLM options are only active when LiteLLM is enabled; otherwise Ark runs in local-only decision mode.
- `Send full file paths to AI?` changes what metadata is sent to AI, not your local file contents.

### If execution is interrupted

Ark saves checkpoints under `<runtime-root>/.ark/state/backup_runs/`. On the next run, you can resume from the latest checkpoint or start a new run.

### Runtime files you may check

- Config: `<runtime-root>/.ark/config.json`
- Log file: `<runtime-root>/.ark/logs/ark.log`
- Run checkpoints/events: `<runtime-root>/.ark/state/backup_runs/`
- Optional runtime AI preference hints: `<runtime-root>/rules.md`

`<runtime-root>/rules.md` is optional plain user-provided preference text.
When remote LLM calls are active, Ark may include this explicit user-provided text in remote AI prompts as suffix/path/directory preference hints.
This file does not change output JSON schema contract.

### Rule sources used in scanning

Ark merges these rules during scanning:

- `src/rules/baseline.ignore`
- `src/rules/suffix_rules.toml`
- per-source `.gitignore`
- optional per-source `.arkignore`

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

No file content means scanned source files being backed up.

Ark may still include explicit user-provided `<runtime-root>/rules.md` text in remote AI prompts when remote LLM calls are active.

`rules.md` remains preference-only guidance and does not relax this boundary.

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
