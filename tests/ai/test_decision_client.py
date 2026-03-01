import src.ai.decision_client as decision_client


def test_llm_suffix_risk_parses_json_payload(monkeypatch) -> None:
    def fake_classify_batch(**_kwargs):
        return '{"items":[{"key":".pdf","decision":"keep","confidence":0.9,"reason":"document"}]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    result = decision_client.llm_suffix_risk(
        [".pdf"],
        model="openai/gpt-4.1-mini",
    )

    assert result[".pdf"]["risk"] == "high_value"
    assert "document" in str(result[".pdf"]["reason"])


def test_llm_suffix_risk_falls_back_to_neutral_on_bad_json(monkeypatch) -> None:
    monkeypatch.setattr(decision_client, "classify_batch", lambda **_kwargs: "not-json")

    result = decision_client.llm_suffix_risk(
        [".tmp"],
        model="openai/gpt-4.1-mini",
    )

    assert result[".tmp"]["risk"] == "neutral"


def test_llm_suffix_risk_parses_fenced_json_payload(monkeypatch) -> None:
    def fake_classify_batch(**_kwargs):
        return """```json
{\"items\":[{\"suffix\":\".md\",\"decision\":\"drop\",\"confidence\":0.7,\"reason\":\"generated\"}]}
```"""

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    result = decision_client.llm_suffix_risk(
        [".md"],
        model="openai/gpt-4.1-mini",
    )

    assert result[".md"]["risk"] == "low_value"
    assert result[".md"]["confidence"] == 0.7


def test_llm_directory_decision_returns_not_sure_on_parse_failure(monkeypatch) -> None:
    monkeypatch.setattr(decision_client, "classify_batch", lambda **_kwargs: "{}")

    result = decision_client.llm_directory_decision(
        "/root/docs",
        ["/root/docs/sub"],
        ["/root/docs/a.txt"],
        model="openai/gpt-4.1-mini",
    )

    assert result["decision"] == "not_sure"


def test_llm_functions_accept_rules_context_kwarg(monkeypatch) -> None:
    def fake_classify_batch(**_kwargs):
        return '{"items":[]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    suffix_result = decision_client.llm_suffix_risk(
        [".pdf"],
        model="openai/gpt-4.1-mini",
        rules_context="Prefer docs",
    )
    path_result = decision_client.llm_path_risk(
        ["/a/b.txt"],
        model="openai/gpt-4.1-mini",
        rules_context="Prefer docs",
    )
    directory_result = decision_client.llm_directory_decision(
        "/root/docs",
        ["/root/docs/sub"],
        ["/root/docs/a.txt"],
        model="openai/gpt-4.1-mini",
        rules_context="Prefer docs",
    )

    assert ".pdf" in suffix_result
    assert "/a/b.txt" in path_result
    assert directory_result["decision"] == "not_sure"


def test_llm_path_risk_includes_rules_block_when_rules_context_present(
    monkeypatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_classify_batch(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return '{"items":[]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    decision_client.llm_path_risk(
        ["/a/b.txt"],
        model="openai/gpt-4.1-mini",
        rules_context="Prefer docs",
    )

    assert "Preference rules from runtime rules.md" in captured["prompt"]
    assert "Prefer docs" in captured["prompt"]


def test_llm_path_risk_omits_rules_block_when_rules_context_empty(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_classify_batch(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return '{"items":[]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    decision_client.llm_path_risk(
        ["/a/b.txt"],
        model="openai/gpt-4.1-mini",
        rules_context="   ",
    )

    assert "Preference rules from runtime rules.md" not in captured["prompt"]


def test_rules_context_is_truncated_with_marker(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_classify_batch(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return '{"items":[]}'

    monkeypatch.setattr(decision_client, "classify_batch", fake_classify_batch)

    decision_client.llm_path_risk(
        ["/a/b.txt"],
        model="openai/gpt-4.1-mini",
        rules_context="x" * 12100,
    )

    assert "...[truncated]" in captured["prompt"]
