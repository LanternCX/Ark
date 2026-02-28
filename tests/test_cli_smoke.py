from typer.testing import CliRunner
from pathlib import Path

import ark.cli as cli_module
from ark.cli import app
from ark.pipeline.config import PipelineConfig


def test_cli_help_contains_ark_description() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Ark backup agent" in result.stdout


def test_cli_root_invokes_main_menu_flow(monkeypatch) -> None:
    runner = CliRunner()
    invoked = False

    def fake_run_main_menu_flow() -> None:
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(cli_module, "run_main_menu_flow", fake_run_main_menu_flow)
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert invoked is True


def test_execute_backup_expands_user_paths(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)

    config = PipelineConfig(
        target="~/backup",
        source_roots=["~/Code"],
        dry_run=True,
        ai_suffix_enabled=False,
        ai_path_enabled=True,
        send_full_path_to_ai=True,
        ai_prune_mode="show_all",
    )

    cli_module._execute_backup(config)

    expected_root = (Path.home() / "Code").resolve()
    expected_target = str((Path.home() / "backup").resolve())
    assert observed["source_roots"] == [expected_root]
    assert observed["target"] == expected_target
    assert observed["send_full_path_to_ai"] is True
    assert observed["ai_prune_mode"] == "show_all"
    assert observed["suffix_risk_fn"] is None
    assert callable(observed["path_risk_fn"])


def test_execute_backup_resumes_latest_matching_run(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeStore:
        def __init__(self, _path):
            pass

        def find_latest_resumable(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            return {"run_id": "run-123", "status": "paused", "state": {}}

        def create_run(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            return "run-new"

        def append_event(self, run_id, stage, event, payload):
            del run_id, stage, event, payload

        def mark_status(self, run_id, status):
            del run_id, status

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "BackupRunStore", FakeStore)
    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)

    config = PipelineConfig(
        target="~/backup",
        source_roots=["~/Code"],
        dry_run=True,
    )

    cli_module._execute_backup(config)

    assert observed["resume"] is True
    assert observed["run_id"] == "run-123"


def test_execute_backup_allows_restart_when_resumable_run_exists(monkeypatch) -> None:
    observed: dict[str, object] = {}
    calls: dict[str, object] = {"created": 0, "marked": []}

    class FakeStore:
        def __init__(self, _path):
            pass

        def find_latest_resumable(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            return {"run_id": "run-old", "status": "paused", "state": {}}

        def create_run(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            calls["created"] = int(calls["created"]) + 1
            return "run-new"

        def append_event(self, run_id, stage, event, payload):
            del run_id, stage, event, payload

        def mark_status(self, run_id, status):
            calls["marked"].append((run_id, status))

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "BackupRunStore", FakeStore)
    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)

    config = PipelineConfig(target="~/backup", source_roots=["~/Code"], dry_run=True)

    cli_module._execute_backup(
        config,
        recovery_choice_prompt=lambda _msg, _choices: "Start new run (keep old)",
    )

    assert observed["resume"] is False
    assert observed["run_id"] == "run-new"
    assert calls["created"] == 1
    assert calls["marked"] == []


def test_execute_backup_allows_discard_when_resumable_run_exists(monkeypatch) -> None:
    observed: dict[str, object] = {}
    calls: dict[str, object] = {"created": 0, "marked": []}

    class FakeStore:
        def __init__(self, _path):
            pass

        def find_latest_resumable(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            return {"run_id": "run-old", "status": "paused", "state": {}}

        def create_run(self, target, source_roots, dry_run):
            del target, source_roots, dry_run
            calls["created"] = int(calls["created"]) + 1
            return "run-new"

        def append_event(self, run_id, stage, event, payload):
            del run_id, stage, event, payload

        def mark_status(self, run_id, status):
            calls["marked"].append((run_id, status))

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "BackupRunStore", FakeStore)
    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)

    config = PipelineConfig(target="~/backup", source_roots=["~/Code"], dry_run=True)

    cli_module._execute_backup(
        config,
        recovery_choice_prompt=lambda _msg, _choices: "Discard old and start new",
    )

    assert observed["resume"] is False
    assert observed["run_id"] == "run-new"
    assert calls["created"] == 1
    assert ("run-old", "discarded") in calls["marked"]


def test_execute_backup_uses_llm_dispatch_when_enabled(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)
    monkeypatch.setattr(
        cli_module,
        "llm_suffix_risk",
        lambda exts, **_kwargs: {
            ext: {"risk": "high_value", "confidence": 1.0, "reason": "ai"}
            for ext in exts
        },
    )
    monkeypatch.setattr(
        cli_module,
        "llm_path_risk",
        lambda paths, **_kwargs: {
            path: {"risk": "neutral", "score": 0.5, "confidence": 1.0, "reason": "ai"}
            for path in paths
        },
    )

    config = PipelineConfig(
        target="~/backup",
        source_roots=["~/Code"],
        dry_run=True,
        llm_enabled=True,
        llm_provider="openai",
        llm_model="openai/gpt-4.1-mini",
        llm_api_key="sk-test",
        ai_suffix_enabled=True,
        ai_path_enabled=True,
    )

    cli_module._execute_backup(config)

    suffix_result = observed["suffix_risk_fn"]([".pdf"])
    path_result = observed["path_risk_fn"](["/tmp/a.txt"])
    assert suffix_result[".pdf"]["reason"] == "ai"
    assert path_result["/tmp/a.txt"]["reason"] == "ai"


def test_execute_backup_falls_back_to_heuristic_when_llm_parse_fails(
    monkeypatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)
    monkeypatch.setattr(
        cli_module,
        "llm_suffix_risk",
        lambda exts, **_kwargs: {
            ext: {"risk": "neutral", "confidence": 0.0, "reason": "LLM parse fallback"}
            for ext in exts
        },
    )

    config = PipelineConfig(
        target="~/backup",
        source_roots=["~/Code"],
        dry_run=True,
        llm_enabled=True,
        llm_provider="openai",
        llm_model="openai/gpt-4.1-mini",
        llm_api_key="sk-test",
        ai_suffix_enabled=True,
        ai_path_enabled=False,
    )

    cli_module._execute_backup(config)

    suffix_result = observed["suffix_risk_fn"]([".pdf"])
    assert suffix_result[".pdf"]["reason"] != "LLM parse fallback"
