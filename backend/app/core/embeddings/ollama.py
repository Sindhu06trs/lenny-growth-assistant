from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.logging_config import logger
from app.core.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingConnectionError,
    EmbeddingTimeoutError,
    EmbeddingProviderError,
    EmbeddingDimensionMismatchError,
)


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama Local Dense Vector Embeddings Provider (e.g. 'nomic-embed-text' or configured model).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        expected_dimension: Optional[int] = None,
        timeout: float = 30.0,
    ):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_EMBED_MODEL
        self._expected_dim = expected_dimension or settings.EMBEDDING_DIMENSION
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def expected_dimension(self) -> int:
        return self._expected_dim

    async def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single text using Ollama /api/embeddings or /api/embed."""
        cleaned = text.replace("\n", " ").strip()
        if not cleaned:
            cleaned = " "

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                # Try the modern /api/embed endpoint first
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": cleaned},
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0]

                # Fallback to legacy /api/embeddings endpoint
                legacy_res = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": cleaned},
                )
                if legacy_res.status_code == 200:
                    data = legacy_res.json()
                    embedding = data.get("embedding", [])
                    if embedding:
                        return embedding
                
                # Check for error status
                if response.status_code == 404 and legacy_res.status_code == 404:
                    raise EmbeddingProviderError(
                        f"Ollama model '{self._model}' not found. Download it via 'ollama pull {self._model}'.",
                        provider=self.provider_name,
                    )

                error_text = response.text or legacy_res.text
                raise EmbeddingProviderError(
                    f"Ollama returned error: {error_text}",
                    provider=self.provider_name,
                )

            except httpx.ConnectError:
                raise EmbeddingConnectionError(
                    f"Could not connect to Ollama embedding service at '{self._base_url}'. "
                    f"Ensure Ollama is running.",
                    provider=self.provider_name,
                )
            except httpx.TimeoutException:
                raise EmbeddingTimeoutError(
                    f"Request to Ollama embedding model '{self._model}' timed out after {self._timeout}s.",
                    provider=self.provider_name,
                )
            except EmbeddingProviderError:
                raise
            except Exception as e:
                raise EmbeddingProviderError(
                    f"Unexpected error communicating with Ollama embeddings: {type(e).__name__}",
                    provider=self.provider_name,
                )

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        if not texts:
            return []

        async with httpx.AsyncClient(timeout=self._timeout * 2) as client:
            try:
                # Try batch input on /api/embed
                cleaned_inputs = [t.replace("\n", " ").strip() or " " for t in texts]
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": cleaned_inputs},
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) == len(texts):
                        return embeddings
            except (httpx.ConnectError, httpx.TimeoutException):
                raise
            except Exception:
                pass

        # Fallback to sequential calls if batch /api/embed is unsupported
        results = []
        for text in texts:
            vec = await self.embed_text(text)
            results.append(vec)
        return results
