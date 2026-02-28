"""Rule loaders for ignore pruning and suffix categorization."""

from __future__ import annotations

import fnmatch
from functools import lru_cache
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

try:
    import pathspec
except ModuleNotFoundError:  # pragma: no cover
    pathspec = None  # type: ignore


RULES_DIR = Path(__file__).resolve().parent
BASELINE_IGNORE_FILE = RULES_DIR / "baseline.ignore"
SUFFIX_RULES_FILE = RULES_DIR / "suffix_rules.toml"


def build_scan_pathspec(source_root: Path):
    """Build gitignore-style matcher from baseline + project rules."""
    lines: list[str] = []
    lines.extend(_read_ignore_file(BASELINE_IGNORE_FILE))
    lines.extend(_read_ignore_file(source_root / ".gitignore"))
    lines.extend(_read_ignore_file(source_root / ".arkignore"))
    return _pathspec_from_lines(lines)


def should_ignore_relpath(spec, relpath: str, is_dir: bool) -> bool:
    """Return whether one relative path should be ignored by rules."""
    normalized = relpath.replace("\\", "/").strip("/")
    if not normalized:
        return False
    if is_dir:
        normalized = f"{normalized}/"
    return bool(spec.match_file(normalized))


def _pathspec_from_lines(lines: list[str]):
    if pathspec is None:
        return _FallbackPathSpec(lines)
    return pathspec.PathSpec.from_lines("gitignore", lines)


class _FallbackPathSpec:
    """Very small gitignore-like matcher when pathspec dependency is unavailable."""

    def __init__(self, patterns: list[str]):
        self.patterns = patterns

    def match_file(self, path: str) -> bool:
        result = False
        normalized = path.replace("\\", "/").strip()
        if not normalized:
            return False
        plain = normalized.rstrip("/")
        for raw in self.patterns:
            negated = raw.startswith("!")
            pattern = raw[1:] if negated else raw
            if _match_pattern(pattern, normalized, plain):
                result = not negated
        return result


def _match_pattern(pattern: str, normalized: str, plain: str) -> bool:
    pat = pattern.replace("\\", "/").strip()
    if not pat:
        return False

    if pat.endswith("/"):
        prefix = pat.rstrip("/")
        if "/" in prefix:
            return plain == prefix or plain.startswith(f"{prefix}/")

        segments = [segment for segment in plain.split("/") if segment]
        for idx, segment in enumerate(segments):
            if segment != prefix:
                continue
            if idx == len(segments) - 1:
                return True
            return True
        return False

    if "/" in pat:
        return fnmatch.fnmatch(normalized, pat) or fnmatch.fnmatch(plain, pat)

    return any(
        [
            fnmatch.fnmatch(plain, pat),
            fnmatch.fnmatch(normalized, pat),
            fnmatch.fnmatch(plain.split("/")[-1], pat),
        ]
    )


def hard_drop_suffixes() -> set[str]:
    """Return suffixes that should be dropped before AI."""
    payload = _load_suffix_rules()
    return {item.lower() for item in payload.get("hard_drop", [])}


def keep_suffixes() -> set[str]:
    """Return local keep suffixes used for fallback mode."""
    payload = _load_suffix_rules()
    return {item.lower() for item in payload.get("keep_default", [])}


def suffix_category(ext: str) -> str:
    """Return category name for one extension."""
    payload = _load_suffix_rules()
    mapping = payload.get("categories", {})
    lowered = ext.lower()
    for category, values in mapping.items():
        if lowered in {item.lower() for item in values}:
            return str(category)
    return "Other"


@lru_cache(maxsize=1)
def _load_suffix_rules() -> dict:
    content = SUFFIX_RULES_FILE.read_bytes()
    data = tomllib.loads(content.decode("utf-8"))
    return data


def _read_ignore_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines
