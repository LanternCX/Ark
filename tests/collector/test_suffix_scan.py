from ark.collector.scanner import collect_suffix_summary


def test_collect_suffix_summary_deduplicates_extensions(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c").write_text("c", encoding="utf-8")

    summary = collect_suffix_summary([tmp_path])

    assert ".txt" in summary.extensions
    assert "c" in summary.no_extension_names
