from ark.tui.llm_catalog import LLM_PROVIDER_GROUPS


def test_each_provider_has_three_recommended_models() -> None:
    for providers in LLM_PROVIDER_GROUPS.values():
        for provider in providers:
            assert len(provider.models) == 3


def test_china_friendly_group_includes_glm_provider() -> None:
    providers = LLM_PROVIDER_GROUPS["China-Friendly"]
    glm_provider = next(
        (item for item in providers if item.provider == "zhipuai"), None
    )

    assert glm_provider is not None
    assert glm_provider.name == "GLM (Zhipu)"
    assert glm_provider.models == (
        "zai/glm-4.7",
        "zai/glm-4.6",
        "zai/glm-4.5",
    )


def test_china_friendly_group_uses_prefixed_deepseek_models() -> None:
    providers = LLM_PROVIDER_GROUPS["China-Friendly"]
    deepseek_provider = next(
        (item for item in providers if item.provider == "deepseek"), None
    )

    assert deepseek_provider is not None
    assert deepseek_provider.models == (
        "deepseek/deepseek-reasoner",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-coder",
    )
