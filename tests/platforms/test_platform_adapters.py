from pathlib import Path

from src.platforms.factory import get_platform_adapter
from src.platforms.macos import MacOSAdapter
from src.platforms.windows import WindowsAdapter


def test_get_platform_adapter_returns_macos_adapter_for_darwin() -> None:
    adapter = get_platform_adapter("darwin")
    assert isinstance(adapter, MacOSAdapter)


def test_get_platform_adapter_returns_windows_adapter_for_win32() -> None:
    adapter = get_platform_adapter("win32")
    assert isinstance(adapter, WindowsAdapter)


def test_macos_adapter_lists_home_and_external_volumes(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    volumes_dir = tmp_path / "Volumes"
    volumes_dir.mkdir()
    external_disk = volumes_dir / "External"
    external_disk.mkdir()

    adapter = MacOSAdapter(home_dir=home_dir, volumes_dir=volumes_dir)

    assert adapter.list_roots() == [home_dir, external_disk]


def test_macos_adapter_iter_files_yields_files_only(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    root.mkdir()
    file_path = root / "a.txt"
    file_path.write_text("ark\n", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    nested_file = nested / "b.md"
    nested_file.write_text("doc\n", encoding="utf-8")

    adapter = MacOSAdapter(home_dir=root, volumes_dir=tmp_path / "none")

    assert list(adapter.iter_files(root)) == [file_path, nested_file]
