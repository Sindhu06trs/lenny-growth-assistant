from typing import Optional
from app.core.config import settings
from app.core.embeddings.base import BaseEmbeddingProvider, EmbeddingProviderError
from app.core.embeddings.openai import OpenAIEmbeddingProvider
from app.core.embeddings.ollama import OllamaEmbeddingProvider


def get_embedding_provider(provider_name: Optional[str] = None) -> BaseEmbeddingProvider:
    """
    Factory function returning an initialized embedding provider instance.
    """
    name = (provider_name or settings.EMBEDDING_PROVIDER or "openai").strip().lower()

    if name == "openai":
        return OpenAIEmbeddingProvider()
    elif name == "ollama":
        return OllamaEmbeddingProvider()
    else:
        raise EmbeddingProviderError(
            f"Unsupported embedding provider: '{name}'. Supported providers: 'openai', 'ollama'."
        )
