from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from app.core.embeddings import (
    BaseEmbeddingProvider,
    OpenAIEmbeddingProvider,
    OllamaEmbeddingProvider,
    get_embedding_provider,
    EmbeddingProviderError,
    EmbeddingDimensionMismatchError,
    EmbeddingAuthError,
    EmbeddingConnectionError,
)


@pytest.mark.asyncio
async def test_ollama_embedding_success_mock():
    """Verifies OllamaEmbeddingProvider embeds text returning 768 dimensions."""
    provider = OllamaEmbeddingProvider(model="nomic-embed-text", expected_dimension=768)
    mock_vec = [0.05] * 768

    with patch.object(provider, "embed_text", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_vec

        res = await provider.embed_text("What is product market fit?")
        assert len(res) == 768
        assert res[0] == 0.05
        assert provider.expected_dimension == 768


@pytest.mark.asyncio
async def test_openai_embedding_success_mock():
    provider = OpenAIEmbeddingProvider(api_key="sk-test-key-12345", dimensions=1536)
    mock_vec = [0.01] * 1536

    mock_item = MagicMock()
    mock_item.index = 0
    mock_item.embedding = mock_vec

    mock_response = MagicMock()
    mock_response.data = [mock_item]

    with patch.object(provider._client.embeddings, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        res = await provider.embed_text("What is product market fit?")
        assert len(res) == 1536
        assert res[0] == 0.01
        assert mock_create.await_count == 1


@pytest.mark.asyncio
async def test_openai_embedding_unconfigured_raises_auth_error():
    provider = OpenAIEmbeddingProvider(api_key=None)
    with patch("app.core.config.settings.OPENAI_API_KEY", None):
        provider._client = None
        with pytest.raises(EmbeddingAuthError):
            await provider.embed_text("Test query")


@pytest.mark.asyncio
async def test_embedding_dimension_validation_detects_mismatch():
    """Verifies that an unexpected dimension raises EmbeddingDimensionMismatchError against 768-dim schema."""
    provider = OllamaEmbeddingProvider(model="nomic-embed-text", expected_dimension=768)
    # Simulate an unexpected 1536 dimensions returned
    mock_1536_vec = [0.05] * 1536

    with patch.object(provider, "embed_text", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_1536_vec

        with pytest.raises(EmbeddingDimensionMismatchError) as exc_info:
            await provider.validate_dimension(expected_dim=768)

        err = exc_info.value
        assert err.actual_dim == 1536
        assert err.expected_dim == 768
        assert "1536 dimensions" in err.message
        assert "768 dimensions" in err.message


@pytest.mark.asyncio
async def test_embedding_dimension_validation_passes_when_matching():
    """Verifies that 768 dimensions passes validation against 768-dim schema."""
    provider = OllamaEmbeddingProvider(model="nomic-embed-text", expected_dimension=768)
    mock_768_vec = [0.02] * 768

    with patch.object(provider, "embed_text", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_768_vec

        # Should complete without raising any exception using default expected dimension
        await provider.validate_dimension(expected_dim=768)
        await provider.validate_dimension()


@pytest.mark.asyncio
async def test_ollama_embedding_connection_error():
    provider = OllamaEmbeddingProvider(base_url="http://127.0.0.1:99999")
    with pytest.raises(EmbeddingConnectionError):
        await provider.embed_text("Test query")


def test_embedding_factory_defaults_to_ollama():
    provider = get_embedding_provider()
    assert provider.provider_name == "ollama"
    assert provider.model_name == "nomic-embed-text"
    assert provider.expected_dimension == 768


def test_embedding_factory_unsupported_provider():
    with pytest.raises(EmbeddingProviderError) as exc_info:
        get_embedding_provider("unsupported_provider_xyz")
    assert "Unsupported embedding provider" in str(exc_info.value)
