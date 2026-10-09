"""Provider-agnostic adapters for hosted and local language models."""

import os

import httpx

from ...models import LLMConfig


def complete(system: str, user: str, config: LLMConfig) -> str:
    """Send a chat completion request to the configured provider.

    :param system: System instruction for the model.
    :param user: User prompt.
    :param config: Provider and model configuration.
    :returns: The model's text response.
    :raises RuntimeError: If a required credential or local service is missing.
    :raises httpx.HTTPStatusError: If the provider rejects the request.
    :raises ValueError: If the provider is unsupported.
    """
    provider, model = config["provider"], config["model"]
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
            "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 1500, "system": system,
                  "messages": [{"role": "user", "content": user}]})
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        r = httpx.post(base_url + "/chat/completions",
            timeout=120, headers={"Authorization": "Bearer " + api_key},
            json={"model": model, "messages": [{"role": "system", "content": system},
                                               {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    if provider == "ollama":
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        try:
            r = httpx.post(ollama_url + "/api/chat", timeout=300,
                json={"model": model, "stream": False, "format": "json",
                      "options": {"num_ctx": 8192, "temperature": 0.2},
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}]})
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {ollama_url}. Start Ollama and verify that model '{model}' is installed."
            ) from e
        r.raise_for_status()
        return r.json()["message"]["content"]
    raise ValueError(f"Unsupported LLM provider: {provider}")
