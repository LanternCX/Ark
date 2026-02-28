from ark.pipeline.config import PipelineConfig


def test_validate_for_execution_requires_provider_and_model_when_llm_enabled() -> None:
    config = PipelineConfig(
        target="X:/ArkBackup",
        source_roots=["."],
        llm_enabled=True,
    )

    errors = config.validate_for_execution()

    assert any("llm provider" in item for item in errors)
    assert any("llm model" in item for item in errors)


def test_validate_for_execution_requires_google_oauth_fields_for_gemini() -> None:
    config = PipelineConfig(
        target="X:/ArkBackup",
        source_roots=["."],
        llm_enabled=True,
        llm_provider="gemini",
        llm_model="gemini/gemini-3-flash",
        llm_auth_method="google_oauth",
    )

    errors = config.validate_for_execution()

    assert any("google client id" in item for item in errors)
    assert any("google client secret" in item for item in errors)
    assert any("google refresh token" in item for item in errors)


def test_validate_for_execution_allows_complete_google_oauth_config() -> None:
    config = PipelineConfig(
        target="X:/ArkBackup",
        source_roots=["."],
        llm_enabled=True,
        llm_provider="gemini",
        llm_model="gemini/gemini-3-flash",
        llm_auth_method="google_oauth",
        google_client_id="id-1",
        google_client_secret="secret-1",
        google_refresh_token="refresh-1",
    )

    errors = config.validate_for_execution()

    assert errors == []
