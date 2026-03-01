"""LiteLLM router abstraction."""

from src.ai.google_oauth import build_google_credentials
from litellm import completion


def classify_batch(
    model: str,
    prompt: str,
    temperature: float = 0.0,
    provider: str = "",
    base_url: str = "",
    api_key: str = "",
    auth_method: str = "api_key",
    google_client_id: str = "",
    google_client_secret: str = "",
    google_refresh_token: str = "",
) -> str:
    """Call LiteLLM chat completion for one batch and return raw content."""
    model_name = model.strip()
    completion_kwargs: dict[str, object] = {
        "model": model_name,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": "You are a strict file-metadata classifier."},
            {"role": "user", "content": prompt},
        ],
    }

    if base_url.strip():
        completion_kwargs["base_url"] = base_url

    if provider == "gemini" and auth_method == "google_oauth":
        credentials = build_google_credentials(
            client_id=google_client_id,
            client_secret=google_client_secret,
            refresh_token=google_refresh_token,
        )
        return _classify_batch_with_google_sdk(
            model=model_name,
            prompt=prompt,
            credentials=credentials,
        )
    elif api_key.strip():
        completion_kwargs["api_key"] = api_key

    response = completion(
        **completion_kwargs,
    )
    return response.choices[0].message.content or ""


def _classify_batch_with_google_sdk(
    model: str, prompt: str, credentials: object
) -> str:
    """Call Gemini with Google official SDK using OAuth credentials."""
    from google import genai

    client = genai.Client(credentials=credentials)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    text = getattr(response, "text", "")
    return text or ""


def check_llm_connectivity(
    model: str,
    provider: str = "",
    base_url: str = "",
    api_key: str = "",
    auth_method: str = "api_key",
    google_client_id: str = "",
    google_client_secret: str = "",
    google_refresh_token: str = "",
) -> tuple[bool, str]:
    """Run a minimal generation request and return connectivity status."""
    try:
        response = classify_batch(
            model=model,
            prompt="hello",
            temperature=0.0,
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            auth_method=auth_method,
            google_client_id=google_client_id,
            google_client_secret=google_client_secret,
            google_refresh_token=google_refresh_token,
        )
        message = response.strip() or "(empty response)"
        if len(message) > 120:
            message = f"{message[:117]}..."
        return True, message
    except Exception as exc:  # pragma: no cover - exercised via tests
        return False, str(exc)
