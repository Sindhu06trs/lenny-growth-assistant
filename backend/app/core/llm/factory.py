import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.llm.base import BaseLLMProvider, ProviderHealth, LLMConfigurationError
from app.core.llm.ollama import OllamaProvider
from app.core.llm.anthropic import AnthropicProvider
from app.core.llm.openai import OpenAIProvider


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function returning the requested LLM provider instance.
    Defaults to settings.DEFAULT_MODEL_PROVIDER if not explicitly specified.
    """
    target = (provider_name or settings.DEFAULT_MODEL_PROVIDER).strip().lower()

    if target == "ollama":
        return OllamaProvider()
    elif target == "anthropic":
        return AnthropicProvider()
    elif target == "openai":
        return OpenAIProvider()
    else:
        raise LLMConfigurationError(
            f"Unsupported LLM provider '{target}'. Supported providers: 'ollama', 'anthropic', 'openai'.",
            provider=target,
        )


async def get_all_providers_status() -> Dict[str, Any]:
    """
    Queries health and configuration across all registered providers concurrently.
    Guaranteed not to raise an exception or fail if a provider is offline.
    """
    providers = {
        "ollama": OllamaProvider(),
        "anthropic": AnthropicProvider(),
        "openai": OpenAIProvider(),
    }

    async def _safe_check(prov: BaseLLMProvider) -> ProviderHealth:
        try:
            return await prov.check_health()
        except Exception as e:
            return ProviderHealth(
                name=prov.name,
                configured=False,
                status="unavailable",
                model=getattr(prov, "model", "unknown"),
                available_models=[],
                detail=f"Health check failed: {type(e).__name__}",
            )

    results = await asyncio.gather(*[_safe_check(p) for p in providers.values()])
    status_map = {res.name: res.model_dump() for res in results}

    return {
        "default_provider": settings.DEFAULT_MODEL_PROVIDER,
        "providers": status_map,
    }
