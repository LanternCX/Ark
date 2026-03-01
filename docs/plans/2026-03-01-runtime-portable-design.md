# Runtime-Local Entry And Packaging Design

## Goal

Refactor Ark to support direct execution from `main.py` without prior installation, move runtime data to the executable/script directory, and extend CI packaging to include macOS artifacts.

## Decisions

1. Runtime root is defined as:
   - directory of `main.py` when running from source
   - directory of executable when running packaged binary
2. Runtime state is stored under `<runtime-root>/.ark/`:
   - config: `<runtime-root>/.ark/config.json`
   - logs: `<runtime-root>/.ark/logs/ark.log`
   - resumable state: `<runtime-root>/.ark/state/backup_runs/`
3. Static rule files are loaded from `<runtime-root>/src/rules/*` when present, with fallback to package-internal defaults.
4. CI release workflow builds both Windows and macOS binaries and bundles runtime-local defaults.

## Architecture Changes

### Runtime path resolver

Create a dedicated runtime path module to centralize all filesystem locations.

- Input priority:
  1. `ARK_RUNTIME_ROOT` env override (for tests and controlled execution)
  2. frozen executable directory (`sys.executable`)
  3. launch script directory (`sys.argv[0]` if it resolves to a file)
  4. current working directory fallback
- Expose typed helpers for config/log/state/rules paths.

### Entry flow

- Add repository-root `main.py` that calls CLI main path, enabling `python3 main.py` runs.
- Keep Typer app in `src/cli.py` and route runtime persistence via runtime path helpers.

### Rules loading

- Resolve rule file paths dynamically at call time.
- Prefer runtime-bundled rule files for portable execution.
- Preserve package fallback for compatibility.

### Packaging workflow

- Convert release build to matrix (`windows-latest`, `macos-latest`).
- Build one-file executable from `main.py`.
- Bundle executable plus runtime files:
  - `.ark/config.json`
  - `src/rules/baseline.ignore`
  - `src/rules/suffix_rules.toml`

## Testing Strategy

1. Add tests for runtime path resolution and runtime-local directories.
2. Update logging tests to assert writes into runtime-local log paths.
3. Update workflow tests to assert macOS packaging and matrix layout.
4. Run targeted tests first, then full `pytest -q`.

## Documentation Scope

Update user and developer docs to replace system-home persistence wording with runtime-local layout:

- `README.md`
- `README.zh-CN.md`
- `docs/architecture.md`
- `docs/architecture.zh-CN.md`
- `docs/privacy-boundary.md`
- `docs/google-oauth-setup.md`
- `docs/google-oauth-setup.zh-CN.md`

## Risks And Mitigations

- Risk: startup directory ambiguity in tests and wrappers.
  - Mitigation: deterministic resolver order + explicit env override.
- Risk: missing external rules in some packaging layouts.
  - Mitigation: package fallback in rules loader.
- Risk: cross-platform artifact naming divergence.
  - Mitigation: matrix metadata (`artifact_suffix`, `binary_name`) drives bundle naming.
