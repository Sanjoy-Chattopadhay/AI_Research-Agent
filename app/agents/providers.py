"""Unified multi-provider LLM client.

Supports Groq, OpenRouter, Hugging Face Inference, Ollama, and OpenAI.
All providers except HF expose an OpenAI-compatible Chat Completions API, so we
just point the `openai` SDK at different base URLs. HF uses its own client.

This gives you free, open-source LLM access by default — sign up for a free key
at https://console.groq.com (recommended) or https://openrouter.ai.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ProviderConfig:
    name: str
    base_url: str | None
    api_key: str | None
    model: str
    supports_tools: bool = True


def available_providers() -> list[ProviderConfig]:
    """Return providers with credentials configured, in default preference order."""
    candidates = {
        "groq": ProviderConfig(
            "groq", "https://api.groq.com/openai/v1", settings.groq_api_key, settings.groq_model
        ),
        "openrouter": ProviderConfig(
            "openrouter",
            "https://openrouter.ai/api/v1",
            settings.openrouter_api_key,
            settings.openrouter_model,
        ),
        "hf": ProviderConfig(
            "hf",
            "https://router.huggingface.co/v1",
            settings.hf_api_key,
            settings.hf_model,
        ),
        "ollama": ProviderConfig(
            "ollama", settings.ollama_base_url, "ollama", settings.ollama_model
        ),
        "openai": ProviderConfig(
            "openai", None, settings.openai_api_key, settings.openai_model
        ),
    }
    order = [settings.default_provider] + [
        p for p in ["groq", "openrouter", "hf", "ollama", "openai"]
        if p != settings.default_provider
    ]
    out = []
    for name in order:
        cfg = candidates.get(name)
        if not cfg:
            continue
        # Ollama is local — assume reachable if no remote keys
        if name == "ollama":
            out.append(cfg)
            continue
        if cfg.api_key:
            out.append(cfg)
    return out


def pick_provider(preference: str = "auto") -> ProviderConfig:
    providers = available_providers()
    if not providers:
        raise RuntimeError(
            "No LLM provider configured. Set GROQ_API_KEY (recommended), "
            "OPENROUTER_API_KEY, HF_API_KEY, OPENAI_API_KEY, or run Ollama locally."
        )
    if preference and preference != "auto":
        for p in providers:
            if p.name == preference:
                return p
        logger.warning("Preferred provider '%s' not configured — falling back to %s", preference, providers[0].name)
    return providers[0]


class LLMClient:
    """Thin async wrapper that targets OpenAI-compatible Chat Completions."""

    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self.client = AsyncOpenAI(
            api_key=cfg.api_key or "not-needed",
            base_url=cfg.base_url,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools and self.cfg.supports_tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return await self.client.chat.completions.create(**kwargs)

    async def stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.cfg.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


def parse_tool_arguments(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
