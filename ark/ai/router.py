"""LiteLLM router abstraction."""

from litellm import completion


def classify_batch(model: str, prompt: str, temperature: float = 0.0) -> str:
    """Call LiteLLM chat completion for one batch and return raw content."""
    response = completion(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You are a strict file-metadata classifier."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""
