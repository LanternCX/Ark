# Privacy Boundary

Ark supports two AI data-sharing modes:

1. Minimal metadata mode
   - basename
   - extension
   - parent_dir_name (last segment)
   - size_bucket
   - mtime_bucket
2. Full path mode (opt-in)
   - full file path strings for suffix and path pruning recommendations

Mode controls are configured from `Settings -> LLM Settings`:

- `Use AI suffix risk classification?`
- `Use AI path pruning suggestions?`
- `Send full file paths to AI?`
- `Hide low-value branches by default?` (UI pruning default only)

Optional runtime preference file:

- Path: `<runtime-root>/rules.md`
- Type: plain user-provided preference text
- Scope: when remote LLM calls are active, Ark may include this explicit user-provided text in remote AI prompts as suffix/path/directory preference hints
- Contract: does not change output JSON schema

No file content means scanned source files being backed up.

Ark may still include explicit user-provided `<runtime-root>/rules.md` text in remote AI prompts when remote LLM calls are active.

`rules.md` does not expand data-sharing scope beyond the configured metadata/path mode.

Ark credentials are configured in local runtime config (`<runtime-root>/.ark/config.json`) via TUI settings.
This includes API keys and Gemini OAuth client/refresh credentials when enabled.

`<runtime-root>` means the directory containing `main.py` (source mode) or the packaged executable (binary mode).
