from typing import Any

import anthropic
import httpx

from overbuild.config import settings

_ANTHROPIC_INPUT_COST_PER_1K = 0.003
_ANTHROPIC_OUTPUT_COST_PER_1K = 0.015


def _normalize_provider(provider: str) -> str:
    value = provider.strip().lower()
    aliases = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "openai": "openai",
        "google": "google",
        "gemini": "google",
    }
    return aliases.get(value, value)


def get_llm_provider() -> str:
    return _normalize_provider(settings.llm_provider)


def get_llm_api_key(provider: str) -> str:
    if settings.llm_api_key:
        return settings.llm_api_key
    if provider == "anthropic":
        return settings.anthropic_api_key
    if provider == "openai":
        return settings.openai_api_key
    if provider == "google":
        return settings.google_api_key
    return ""


def has_llm_config() -> bool:
    provider = get_llm_provider()
    return bool(get_llm_api_key(provider))


def extract_json_payload(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def _estimate_anthropic_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * _ANTHROPIC_INPUT_COST_PER_1K
        + output_tokens * _ANTHROPIC_OUTPUT_COST_PER_1K
    ) / 1000


async def _call_anthropic(system_prompt: str, user_message: str, max_tokens: int) -> tuple[str, float]:
    client = anthropic.AsyncAnthropic(api_key=get_llm_api_key("anthropic"))
    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text_parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", "") != "text":
            continue
        text_value = getattr(block, "text", None)
        if isinstance(text_value, str):
            text_parts.append(text_value)

    input_tokens = int(getattr(response.usage, "input_tokens", 0))
    output_tokens = int(getattr(response.usage, "output_tokens", 0))
    cost = _estimate_anthropic_cost(input_tokens, output_tokens)
    return "".join(text_parts), cost


async def _call_openai(system_prompt: str, user_message: str, max_tokens: int) -> tuple[str, float]:
    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {get_llm_api_key('openai')}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])
    if not choices:
        raise ValueError("OpenAI response did not include any choices")

    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content, 0.0
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "".join(text_parts), 0.0
    raise ValueError("OpenAI response content was not a supported format")


async def _call_google(system_prompt: str, user_message: str, max_tokens: int) -> tuple[str, float]:
    model = settings.llm_model
    model_path = model if model.startswith("models/") else f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent"
    params = {"key": get_llm_api_key("google")}
    payload: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "maxOutputTokens": max_tokens,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Google response did not include any candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            text_parts.append(part["text"])
    if not text_parts:
        raise ValueError("Google response did not include text content")
    return "".join(text_parts), 0.0


async def call_llm_json(system_prompt: str, user_message: str, max_tokens: int) -> tuple[str, float]:
    provider = get_llm_provider()
    api_key = get_llm_api_key(provider)
    if not api_key:
        raise ValueError(f"Missing API key for provider '{provider}'")

    if provider == "anthropic":
        return await _call_anthropic(system_prompt, user_message, max_tokens)
    if provider == "openai":
        return await _call_openai(system_prompt, user_message, max_tokens)
    if provider == "google":
        return await _call_google(system_prompt, user_message, max_tokens)
    raise ValueError(
        f"Unsupported provider '{settings.llm_provider}'. Use anthropic, openai, or google."
    )
