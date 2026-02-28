# Privacy Boundary

Ark sends only minimal metadata to AI models:

- basename
- extension
- parent_dir_name (last segment)
- size_bucket
- mtime_bucket

Ark does not send file content.

Ark credentials are configured in local runtime config (`~/.ark/config.json`) via TUI settings.
This includes API keys and Gemini OAuth client/refresh credentials when enabled.
