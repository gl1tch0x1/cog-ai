"""Module 2: Omni-LLM — provider-agnostic client with auto-detection."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from secagents.vault.env_loader import detect_provider_from_key, mask_secret
from secagents.infra.rate_limiting import get_rate_limiter


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    tokens_used: int = 0


DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "openai_compatible": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "groq": "llama-3.1-70b-versatile",
    "google": "gemini-1.5-flash",
    "openrouter": "openai/gpt-4o-mini",
    "xai": "grok-beta",
    "ollama": "llama3",
}


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str | None = None
    model: str | None = None


class OmniLLM:
    """
    Universal LLM client. No --llm-provider flag required.
    Detects provider from key prefix; supports multiple keys for consensus.
    """

    def __init__(self, providers: list[ProviderConfig] | None = None):
        self.providers = providers or self._discover_providers()
        self._client = httpx.AsyncClient(timeout=120)

    def _discover_providers(self) -> list[ProviderConfig]:
        configs: list[ProviderConfig] = []
        bulk = os.environ.get("LLM_API_KEYS", "")
        keys: list[str] = [k.strip() for k in bulk.split(",") if k.strip()] if bulk else []
        if not keys:
            for env in (
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "GROQ_API_KEY",
                "DEEPSEEK_API_KEY",
                "GEMINI_API_KEY",
                "OPENROUTER_API_KEY",
            ):
                val = os.environ.get(env, "").strip()
                if val:
                    keys.append(val)
        for key in keys:
            name = detect_provider_from_key(key)
            configs.append(ProviderConfig(name=name, api_key=key))
        # Local Ollama fallback — only if OLLAMA_HOST is explicitly set
        if not configs:
            ollama_host = os.environ.get("OLLAMA_HOST", "").strip()
            if ollama_host:
                configs.append(
                    ProviderConfig(name="ollama", api_key="ollama", base_url=ollama_host)
                )
        return configs

    async def complete(
        self,
        messages: list[LLMMessage],
        provider: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        cfg = self._select_provider(provider)
        if not cfg:
            raise RuntimeError(
                "No LLM provider configured. Set LLM_API_KEYS or OPENAI_API_KEY in .env"
            )

        await get_rate_limiter().check(cfg.name)
        model = model or cfg.model or DEFAULT_MODELS.get(cfg.name, "gpt-4o-mini")

        if cfg.name == "anthropic":
            return await self._anthropic(cfg, messages, model, max_tokens)
        if cfg.name == "google":
            return await self._gemini(cfg, messages, model, max_tokens)
        if cfg.name == "ollama":
            return await self._ollama(cfg, messages, model, max_tokens)
        if cfg.name == "groq":
            return await self._openai_compatible(
                cfg, messages, model, max_tokens, "https://api.groq.com/openai/v1"
            )
        if cfg.name == "openrouter":
            return await self._openai_compatible(
                cfg, messages, model, max_tokens, "https://openrouter.ai/api/v1"
            )
        base = cfg.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return await self._openai_compatible(cfg, messages, model, max_tokens, base)

    def _select_provider(self, name: str | None) -> ProviderConfig | None:
        if not self.providers:
            return None
        if name:
            for p in self.providers:
                if p.name == name:
                    return p
        return self.providers[0]

    async def _openai_compatible(
        self,
        cfg: ProviderConfig,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int,
        base_url: str,
    ) -> LLMResponse:
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
        }
        resp = await self._client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            provider=cfg.name,
            model=model,
            tokens_used=usage.get("total_tokens", 0),
        )

    async def _anthropic(
        self,
        cfg: ProviderConfig,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        system = ""
        msgs = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                msgs.append({"role": m.role, "content": m.content})
        body: dict = {"model": model, "max_tokens": max_tokens, "messages": msgs}
        if system:
            body["system"] = system
        resp = await self._client.post(
            "https://api.anthropic.com/v1/messages",
            json=body,
            headers={
                "x-api-key": cfg.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["content"][0]["text"]
        return LLMResponse(content=content, provider="anthropic", model=model)

    async def _gemini(
        self,
        cfg: ProviderConfig,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        text = "\n".join(f"{m.role}: {m.content}" for m in messages)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={cfg.api_key}"
        )
        resp = await self._client.post(
            url,
            json={
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(content=content, provider="google", model=model)

    async def _ollama(
        self,
        cfg: ProviderConfig,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        base = (cfg.base_url or "http://localhost:11434").rstrip("/")
        resp = await self._client.post(
            f"{base}/api/chat",
            json={
                "model": model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        return LLMResponse(content=content, provider="ollama", model=model)

    async def aclose(self) -> None:
        await self._client.aclose()

    def masked_providers(self) -> list[str]:
        return [f"{p.name}:{mask_secret(p.api_key)}" for p in self.providers]
