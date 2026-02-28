"""LiteLLM provider presets used by Ark TUI settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMProviderPreset:
    """Preset describing one LiteLLM provider option."""

    name: str
    provider: str
    models: tuple[str, str, str]
    requires_api_key: bool = True
    base_url: str = ""
    allow_base_url: bool = False

    @property
    def default_model(self) -> str:
        """Return the first recommended model."""
        return self.models[0]


LLM_PROVIDER_GROUPS: dict[str, list[LLMProviderPreset]] = {
    "OpenAI & Compatible": [
        LLMProviderPreset(
            name="OpenAI",
            provider="openai",
            models=("openai/gpt-4.1", "openai/gpt-4o", "openai/gpt-4.1-mini"),
        ),
        LLMProviderPreset(
            name="OpenRouter",
            provider="openrouter",
            models=(
                "openai/gpt-4.1",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.5-pro",
            ),
            base_url="https://openrouter.ai/api/v1",
        ),
        LLMProviderPreset(
            name="Together AI",
            provider="together_ai",
            models=(
                "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "together_ai/deepseek-ai/DeepSeek-V3",
                "together_ai/Qwen/Qwen2.5-72B-Instruct-Turbo",
            ),
            base_url="https://api.together.xyz/v1",
        ),
        LLMProviderPreset(
            name="Fireworks AI",
            provider="fireworks_ai",
            models=(
                "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
                "fireworks_ai/accounts/fireworks/models/llama-v3p1-70b-instruct",
                "fireworks_ai/accounts/fireworks/models/mixtral-8x22b-instruct",
            ),
            base_url="https://api.fireworks.ai/inference/v1",
        ),
    ],
    "Frontier Models": [
        LLMProviderPreset(
            name="Anthropic",
            provider="anthropic",
            models=(
                "anthropic/claude-opus-4-1",
                "anthropic/claude-sonnet-4",
                "anthropic/claude-3-5-sonnet-latest",
            ),
        ),
        LLMProviderPreset(
            name="Google Gemini",
            provider="gemini",
            models=(
                "gemini/gemini-3-flash",
                "gemini/gemini-2.5-pro",
                "gemini/gemini-2.5-flash",
            ),
        ),
        LLMProviderPreset(
            name="Mistral",
            provider="mistral",
            models=(
                "mistral/mistral-large-latest",
                "mistral/mistral-medium-latest",
                "mistral/ministral-8b-latest",
            ),
        ),
        LLMProviderPreset(
            name="Groq",
            provider="groq",
            models=(
                "groq/llama-3.3-70b-versatile",
                "groq/llama-3.1-70b-versatile",
                "groq/qwen-qwq-32b",
            ),
        ),
    ],
    "China-Friendly": [
        LLMProviderPreset(
            name="DeepSeek",
            provider="deepseek",
            models=(
                "deepseek/deepseek-reasoner",
                "deepseek/deepseek-chat",
                "deepseek/deepseek-coder",
            ),
        ),
        LLMProviderPreset(
            name="GLM (Zhipu)",
            provider="zhipuai",
            models=("zai/glm-4.7", "zai/glm-4.6", "zai/glm-4.5"),
            base_url="https://open.bigmodel.cn/api/paas/v4/",
        ),
        LLMProviderPreset(
            name="Qwen (Ali Tongyi)",
            provider="qwen",
            models=("qwen/qwen-max", "qwen/qwen-plus", "qwen/qwen-turbo"),
        ),
        LLMProviderPreset(
            name="Moonshot",
            provider="moonshot",
            models=(
                "moonshot/moonshot-v1-128k",
                "moonshot/moonshot-v1-32k",
                "moonshot/moonshot-v1-8k",
            ),
        ),
        LLMProviderPreset(
            name="MiniMax",
            provider="minimax",
            models=(
                "minimax/abab6.5s-chat",
                "minimax/abab6.5-chat",
                "minimax/abab5.5-chat",
            ),
        ),
    ],
    "Research / Web": [
        LLMProviderPreset(
            name="Perplexity",
            provider="perplexity",
            models=(
                "perplexity/sonar-pro",
                "perplexity/sonar-reasoning-pro",
                "perplexity/pplx-70b-online",
            ),
        ),
        LLMProviderPreset(
            name="Cohere",
            provider="cohere",
            models=(
                "cohere/command-a-03-2025",
                "cohere/command-r-plus",
                "cohere/command-r",
            ),
        ),
    ],
    "Local & Custom": [
        LLMProviderPreset(
            name="Ollama (local)",
            provider="ollama",
            models=("ollama/llama3.3", "ollama/qwen2.5:32b", "ollama/deepseek-r1:14b"),
            requires_api_key=False,
            base_url="http://localhost:11434",
            allow_base_url=True,
        ),
        LLMProviderPreset(
            name="OpenAI-Compatible (custom)",
            provider="custom",
            models=(
                "openai/gpt-4.1",
                "anthropic/claude-sonnet-4",
                "gemini/gemini-2.5-pro",
            ),
            allow_base_url=True,
        ),
    ],
}


def find_provider_group(provider: str) -> str | None:
    """Return provider group name for provider id."""
    for group_name, presets in LLM_PROVIDER_GROUPS.items():
        if any(p.provider == provider for p in presets):
            return group_name
    return None
