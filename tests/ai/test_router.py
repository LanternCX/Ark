from ark.ai import router


def test_check_llm_connectivity_sends_hello_and_returns_reply(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_classify_batch(**kwargs):
        captured.update(kwargs)
        return "hello from model"

    monkeypatch.setattr(router, "classify_batch", fake_classify_batch)

    ok, message = router.check_llm_connectivity(model="openai/gpt-4.1-mini")

    assert ok is True
    assert captured["prompt"] == "hello"
    assert "hello from model" in message
