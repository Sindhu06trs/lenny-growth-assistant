import abc
from typing import List, Optional


class EmbeddingProviderError(Exception):
    """Base exception for all embedding provider errors."""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider


class EmbeddingDimensionMismatchError(EmbeddingProviderError):
    """Raised when an embedding provider returns dimensions differing from pgvector schema."""

    def __init__(self, actual_dim: int, expected_dim: int, model: str, provider: str):
        message = (
            f"Embedding model '{model}' ({provider}) produced {actual_dim} dimensions, "
            f"but PostgreSQL 'transcript_chunks.embedding' requires {expected_dim} dimensions. "
            f"Please configure a {expected_dim}-dimensional embedding model (e.g., OpenAI 'text-embedding-3-small') "
            f"or create an Alembic migration to update the column dimension."
        )
        super().__init__(message, provider=provider)
        self.actual_dim = actual_dim
        self.expected_dim = expected_dim
        self.model = model


class EmbeddingConnectionError(EmbeddingProviderError):
    """Raised when the embedding service cannot be reached."""
    pass


class EmbeddingAuthError(EmbeddingProviderError):
    """Raised when API credentials for the embedding provider are invalid or missing."""
    pass


class EmbeddingTimeoutError(EmbeddingProviderError):
    """Raised when the embedding request times out."""
    pass


class BaseEmbeddingProvider(abc.ABC):
    """
    Abstract Base Class for all dense vector embedding providers.
    Ensures normalized interface, dimension validation, and safe error handling.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'openai', 'ollama')."""
        pass

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """Name of the configured embedding model."""
        pass

    @property
    @abc.abstractmethod
    def expected_dimension(self) -> int:
        """Expected dimension for this provider/model configuration."""
        pass

    @abc.abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Embeds a single string into a high-dimensional dense vector.
        """
        pass

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of strings into high-dimensional dense vectors.
        """
        pass

    async def validate_dimension(self, expected_dim: Optional[int] = None) -> None:
        """
        Sends a test phrase to verify that the generated embedding matches the database column dimension.
        """
        target_dim = expected_dim if expected_dim is not None else self.expected_dimension
        sample_vec = await self.embed_text("Test embedding dimension validation.")
        actual_dim = len(sample_vec)
        if actual_dim != target_dim:
            raise EmbeddingDimensionMismatchError(
                actual_dim=actual_dim,
                expected_dim=target_dim,
                model=self.model_name,
                provider=self.provider_name,
            )
