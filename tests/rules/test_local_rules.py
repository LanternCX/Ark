from pathlib import Path

import ark.rules.local_rules as local_rules


def test_build_scan_pathspec_works_without_pathspec_dependency(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / ".gitignore").write_text(".venv/\n", encoding="utf-8")

    monkeypatch.setattr(local_rules, "pathspec", None)
    spec = local_rules.build_scan_pathspec(source_root)

    assert local_rules.should_ignore_relpath(spec, ".venv", is_dir=True) is True
    assert (
        local_rules.should_ignore_relpath(spec, "docs/readme.md", is_dir=False) is False
    )


def test_fallback_matcher_ignores_nested_node_modules(monkeypatch) -> None:
    monkeypatch.setattr(local_rules, "pathspec", None)
    spec = local_rules._FallbackPathSpec(["node_modules/"])

    assert (
        local_rules.should_ignore_relpath(
            spec,
            ".opencode/node_modules/zod/v4/locales/en.ts",
            is_dir=False,
        )
        is True
    )
    assert (
        local_rules.should_ignore_relpath(spec, "src/app/main.py", is_dir=False)
        is False
    )
