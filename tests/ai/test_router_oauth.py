import src.ai.router as router_module


def test_classify_batch_uses_google_sdk_for_gemini_oauth(monkeypatch) -> None:
    class FakeCredentials:
        token = "access-1"

    def fake_build_google_credentials(
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> object:
        assert client_id == "id-1"
        assert client_secret == "secret-1"
        assert refresh_token == "refresh-1"
        return FakeCredentials()

    def fake_classify_batch_with_google_sdk(
        model: str,
        prompt: str,
        credentials: object,
    ) -> str:
        assert model == "gemini/gemini-3-flash"
        assert prompt == "hello"
        assert getattr(credentials, "token", "") == "access-1"
        return "ok"

    monkeypatch.setattr(
        router_module,
        "build_google_credentials",
        fake_build_google_credentials,
    )
    monkeypatch.setattr(
        router_module,
        "_classify_batch_with_google_sdk",
        fake_classify_batch_with_google_sdk,
    )

    result = router_module.classify_batch(
        model="gemini/gemini-3-flash",
        prompt="hello",
        provider="gemini",
        auth_method="google_oauth",
        google_client_id="id-1",
        google_client_secret="secret-1",
        google_refresh_token="refresh-1",
    )

    assert result == "ok"


def test_check_llm_connectivity_reports_failure(monkeypatch) -> None:
    def fake_classify_batch(**_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(router_module, "classify_batch", fake_classify_batch)

    ok, message = router_module.check_llm_connectivity(
        model="zai/glm-4.5",
        provider="zhipuai",
        api_key="sk-any",
    )

    assert ok is False
    assert "network down" in message


def test_classify_batch_passes_glm_prefixed_model_verbatim(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Message:
        def __init__(self, content: str) -> None:
            self.content = content

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = _Message(content)

    class _Response:
        def __init__(self, content: str) -> None:
            self.choices = [_Choice(content)]

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _Response("pong")

    monkeypatch.setattr(router_module, "completion", fake_completion)

    result = router_module.classify_batch(
        model="zai/glm-4.5",
        prompt="hello",
        provider="zhipuai",
        api_key="sk-test",
    )

    assert result == "pong"
    assert captured["model"] == "zai/glm-4.5"


def test_classify_batch_passes_deepseek_prefixed_model_verbatim(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Message:
        def __init__(self, content: str) -> None:
            self.content = content

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = _Message(content)

    class _Response:
        def __init__(self, content: str) -> None:
            self.choices = [_Choice(content)]

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _Response("pong")

    monkeypatch.setattr(router_module, "completion", fake_completion)

    result = router_module.classify_batch(
        model="deepseek/deepseek-chat",
        prompt="hello",
        provider="deepseek",
        api_key="sk-test",
    )

    assert result == "pong"
    assert captured["model"] == "deepseek/deepseek-chat"
