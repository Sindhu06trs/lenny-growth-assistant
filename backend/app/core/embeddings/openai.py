import os
from typing import List, Optional
import openai
from openai import AsyncOpenAI, AuthenticationError, APIConnectionError, APITimeoutError, APIError

from app.core.config import settings
from app.core.logging_config import logger
from app.core.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingAuthError,
    EmbeddingConnectionError,
    EmbeddingTimeoutError,
    EmbeddingProviderError,
)


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Dense Vector Embeddings Provider (e.g. 'text-embedding-3-small').
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        timeout: float = 30.0,
    ):
        self._api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self._model = model or settings.EMBEDDING_MODEL
        self._dimensions = dimensions or settings.EMBEDDING_DIMENSION
        self._timeout = timeout

        if not self._api_key or self._api_key.strip() in ("", "your_openai_api_key_here"):
            self._client = None
        else:
            self._client = AsyncOpenAI(api_key=self._api_key, timeout=self._timeout)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def expected_dimension(self) -> int:
        return self._dimensions

    def is_configured(self) -> bool:
        return self._client is not None

    async def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single text."""
        batch_res = await self.embed_batch([text])
        return batch_res[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of texts."""
        if not texts:
            return []

        if not self.is_configured():
            raise EmbeddingAuthError(
                "OpenAI API key is missing or not configured for embeddings. "
                "Set OPENAI_API_KEY in your environment or .env file.",
                provider=self.provider_name,
            )

        # Clean strings without removing semantic meaning
        cleaned_inputs = [t.replace("\n", " ").strip() for t in texts]
        # Replace empty strings with a single space to avoid OpenAI 400 error
        cleaned_inputs = [t if t else " " for t in cleaned_inputs]

        try:
            # text-embedding-3-small supports the 'dimensions' parameter
            kwargs = {"model": self._model, "input": cleaned_inputs}
            if "text-embedding-3" in self._model:
                kwargs["dimensions"] = self._dimensions

            response = await self._client.embeddings.create(**kwargs)
            # Sort by index to maintain ordering
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except AuthenticationError as e:
            logger.warning(f"OpenAI embedding auth failure: {type(e).__name__}")
            raise EmbeddingAuthError("Invalid OpenAI API credentials.", provider=self.provider_name)
        except APITimeoutError as e:
            logger.warning(f"OpenAI embedding timeout: {type(e).__name__}")
            raise EmbeddingTimeoutError("OpenAI embedding request timed out.", provider=self.provider_name)
        except APIConnectionError as e:
            logger.warning(f"OpenAI embedding connection error: {type(e).__name__}")
            raise EmbeddingConnectionError("Unable to connect to OpenAI embedding API.", provider=self.provider_name)
        except APIError as e:
            logger.warning(f"OpenAI embedding API error: {e.message}")
            raise EmbeddingProviderError(f"OpenAI embedding error: {e.message}", provider=self.provider_name)
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI embedding: {type(e).__name__}", exc_info=True)
            raise EmbeddingProviderError(f"Unexpected embedding failure: {type(e).__name__}", provider=self.provider_name)
