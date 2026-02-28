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

Ark does not send file content.

Ark credentials are configured in local runtime config (`~/.ark/config.json`) via TUI settings.
This includes API keys and Gemini OAuth client/refresh credentials when enabled.
