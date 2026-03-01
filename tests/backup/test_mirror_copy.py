from src.backup.executor import mirror_copy_one


def test_mirror_copy_one_recreates_relative_path(tmp_path) -> None:
    src_root = tmp_path / "C"
    src_root.mkdir()
    src = src_root / "Users" / "me" / "doc.txt"
    src.parent.mkdir(parents=True)
    src.write_text("hello", encoding="utf-8")

    dst_root = tmp_path / "backup"
    mirror_copy_one(src_root, src, dst_root)

    assert (dst_root / "C" / "Users" / "me" / "doc.txt").exists()
