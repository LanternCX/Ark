from pathlib import Path


def test_verify_script_exists_and_is_executable() -> None:
    script = Path("scripts/verify.sh")
    assert script.exists()
