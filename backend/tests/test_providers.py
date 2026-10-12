import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx
import anthropic
import openai

from app.main import app
from app.core.llm import (
    get_llm_provider,
    get_all_providers_status,
    LLMResponse,
    LLMConfigurationError,
    LLMConnectionError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTimeoutError,
)
from app.core.llm.ollama import OllamaProvider
from app.core.llm.anthropic import AnthropicProvider
from app.core.llm.openai import OpenAIProvider

client = TestClient(app)


# ------------------------------------------------------------------------------
# 1. Provider Status Endpoint Tests
# ------------------------------------------------------------------------------

def test_provider_status_endpoint_structure():
    """
    Test GET /api/providers/status returns 200 with all supported providers
    and never leaks secrets or API keys.
    """
    response = client.get("/api/providers/status")
    assert response.status_code == 200

    data = response.json()
    assert "default_provider" in data
    assert "providers" in data

    providers = data["providers"]
    assert "ollama" in providers
    assert "anthropic" in providers
    assert "openai" in providers

    for name, p_info in providers.items():
        assert p_info["name"] == name
        assert isinstance(p_info["configured"], bool)
        assert p_info["status"] in ("connected", "configured", "unavailable", "authentication_failed", "model_not_found")
        assert "model" in p_info
        # Critical security check: Ensure no keys/secrets leaked
        assert "api_key" not in p_info
        assert "password" not in p_info


@pytest.mark.asyncio
async def test_ollama_health_when_service_unavailable():
    """
    Test Ollama health check returns status='unavailable' when service cannot be reached.
    """
    provider = OllamaProvider(base_url="http://127.0.0.1:59999", model="llama3.1:8b")
    health = await provider.check_health()
    assert health.status == "unavailable"
    assert "not reachable" in (health.detail or "").lower() or "failed" in (health.detail or "").lower()


@pytest.mark.asyncio
async def test_ollama_health_when_model_missing():
    """
    Test Ollama health check returns status='model_not_found' when service is up but model is not pulled.
    """
    provider = OllamaProvider(base_url="http://localhost:11434", model="nonexistent-model:99b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "nomic-embed-text:latest"}, {"name": "mistral:latest"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        health = await provider.check_health()
        assert health.status == "model_not_found"
        assert "not installed" in health.detail.lower()


@pytest.mark.asyncio
async def test_ollama_health_when_connected_successfully():
    """
    Test Ollama health check returns status='connected' when model is present.
    """
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "llama3.2:3b"}, {"name": "nomic-embed-text:latest"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        health = await provider.check_health()
        assert health.status == "connected"
        assert "llama3.2:3b" in health.available_models


# ------------------------------------------------------------------------------
# 2. Provider Abstraction & Unit Tests
# ------------------------------------------------------------------------------

def test_factory_invalid_provider_raises_configuration_error():
    """
    Test factory raises LLMConfigurationError for unknown provider.
    """
    with pytest.raises(LLMConfigurationError) as exc_info:
        get_llm_provider("unknown-quantum-llm")
    assert "Unsupported LLM provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_generate_response_success():
    """
    Test Ollama chat generation with mocked HTTP response.
    """
    provider = OllamaProvider(model="llama3.2:3b")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"content": "Retention can be improved through activation hooks."},
        "total_duration": 1500000,
        "eval_count": 25,
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await provider.generate_response(
            messages=[{"role": "user", "content": "How do we improve retention?"}],
            system_prompt="You are Lenny Assistant.",
        )
        assert res.provider == "ollama"
        assert res.model == "llama3.2:3b"
        assert "Retention can be improved" in res.text


@pytest.mark.asyncio
async def test_ollama_generate_connection_error():
    """
    Test Ollama raises LLMConnectionError on network connection failure.
    """
    provider = OllamaProvider()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(LLMConnectionError):
            await provider.generate_response(messages=[{"role": "user", "content": "Hello"}])


@pytest.mark.asyncio
async def test_ollama_generate_model_not_found():
    """
    Test Ollama raises LLMModelNotFoundError when Ollama returns 404.
    """
    provider = OllamaProvider(model="missing-model:latest")
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"error": "model 'missing-model:latest' not found"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        with pytest.raises(LLMModelNotFoundError):
            await provider.generate_response(messages=[{"role": "user", "content": "Hello"}])


@pytest.mark.asyncio
async def test_ollama_generate_timeout():
    """
    Test Ollama raises LLMTimeoutError when request times out.
    """
    provider = OllamaProvider()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(LLMTimeoutError):
            await provider.generate_response(messages=[{"role": "user", "content": "Hello"}])


@pytest.mark.asyncio
async def test_anthropic_generate_response_mock():
    """
    Test Anthropic provider with mocked AsyncAnthropic SDK client.
    """
    provider = AnthropicProvider(api_key="sk-ant-test-key-mock", model="claude-3-5-sonnet-20241022")

    mock_content_block = MagicMock()
    mock_content_block.text = "Focus on the first-mile experience and setup moment."

    mock_msg_resp = MagicMock()
    mock_msg_resp.content = [mock_content_block]
    mock_msg_resp.usage.input_tokens = 50
    mock_msg_resp.usage.output_tokens = 20

    with patch("anthropic.AsyncAnthropic") as MockClientClass:
        mock_instance = MockClientClass.return_value
        mock_instance.messages.create = AsyncMock(return_value=mock_msg_resp)

        res = await provider.generate_response(
            messages=[{"role": "user", "content": "What is activation?"}],
            system_prompt="You are a growth advisor.",
        )
        assert res.provider == "anthropic"
        assert "first-mile experience" in res.text


@pytest.mark.asyncio
async def test_anthropic_auth_failure_raises_normalized_error():
    """
    Test Anthropic raises LLMAuthenticationError when SDK raises AuthenticationError.
    """
    provider = AnthropicProvider(api_key="sk-ant-invalid-key")

    mock_req = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("anthropic.AsyncAnthropic") as MockClientClass:
        mock_instance = MockClientClass.return_value
        mock_instance.messages.create = AsyncMock(
            side_effect=anthropic.AuthenticationError(
                message="Invalid API key", response=mock_resp, body=None
            )
        )
        with pytest.raises(LLMAuthenticationError):
            await provider.generate_response(messages=[{"role": "user", "content": "Test"}])


@pytest.mark.asyncio
async def test_openai_generate_response_mock():
    """
    Test OpenAI provider with mocked AsyncOpenAI SDK client.
    """
    provider = OpenAIProvider(api_key="sk-proj-test-key-mock", model="gpt-4o")

    mock_choice = MagicMock()
    mock_choice.message.content = "Growth loops compound user actions into new acquisition."

    mock_comp_resp = MagicMock()
    mock_comp_resp.choices = [mock_choice]
    mock_comp_resp.usage.prompt_tokens = 40
    mock_comp_resp.usage.completion_tokens = 20
    mock_comp_resp.usage.total_tokens = 60

    with patch("openai.AsyncOpenAI") as MockClientClass:
        mock_instance = MockClientClass.return_value
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_comp_resp)

        res = await provider.generate_response(
            messages=[{"role": "user", "content": "Explain growth loops."}],
            system_prompt="You are an expert.",
        )
        assert res.provider == "openai"
        assert "Growth loops compound" in res.text


# ------------------------------------------------------------------------------
# 3. Chat Endpoint Integration & Persistence Tests
# ------------------------------------------------------------------------------

def test_chat_with_mocked_successful_provider():
    """
    Test POST /api/chat invokes provider, saves user and assistant turns,
    and returns 200 with status='success'.
    """
    mock_provider = MagicMock()
    mock_provider.name = "ollama"
    mock_provider.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="PMF happens when cohort retention curves flatten out.",
            provider="ollama",
            model="llama3.2:3b"
        )
    )

    with patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        payload = {
            "message": "When do you know you have product-market fit?",
            "provider": "ollama"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "PMF happens when cohort retention curves flatten out." in data["message"]
        assert data["sources"] == []  # Not fabricated


def test_chat_followup_context_passed_to_provider():
    """
    Test that multiple turns in the same session load prior history
    and pass it to the provider.
    """
    session_id = "session-followup-test-999"

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="Sure, here is how you calculate that.",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022"
        )
    )

    with patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        # Turn 1
        res1 = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "What is net revenue retention?",
            "provider": "anthropic"
        })
        assert res1.status_code == 200

        # Turn 2
        res2 = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "How do I calculate it with an example?",
            "provider": "anthropic"
        })
        assert res2.status_code == 200

        # Verify the second call received the first turn in messages payload
        call_args = mock_provider.generate_response.call_args
        passed_messages = call_args.kwargs.get("messages", [])
        
        # Should have: user msg 1, assistant msg 1, user msg 2
        contents = [m["content"] for m in passed_messages]
        assert any("What is net revenue retention?" in c for c in contents)
        assert any("How do I calculate it with an example?" in c for c in contents)


def test_chat_safe_error_handling_when_provider_fails():
    """
    Test that when a provider fails with connection error, the chat endpoint
    handles it cleanly, returns status='unavailable', and leaks zero secrets.
    """
    mock_provider = MagicMock()
    mock_provider.name = "ollama"
    mock_provider.generate_response = AsyncMock(
        side_effect=LLMConnectionError("Ollama daemon is down", provider="ollama")
    )

    with patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        payload = {
            "message": "Tell me about viral growth.",
            "provider": "ollama"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "unavailable"
        assert "Could not reach model provider 'ollama'" in data["message"]


def test_ollama_chat_does_not_require_anthropic_api_key():
    """
    Test that Ollama provider completes chat responses successfully
    even when ANTHROPIC_API_KEY is not set or is an empty/placeholder value.
    """
    mock_provider = MagicMock()
    mock_provider.name = "ollama"
    mock_provider.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="Retention can be evaluated through cohort survival analysis.",
            provider="ollama",
            model="llama3.2:3b",
        )
    )

    with patch("app.core.config.settings.ANTHROPIC_API_KEY", None), \
         patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        payload = {
            "message": "Explain retention curves.",
            "provider": "ollama"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["provider"] == "ollama"
        assert "cohort survival" in data["message"]


@pytest.mark.asyncio
async def test_ollama_provider_health_detects_llama32_and_tags():
    """
    Test that OllamaProvider accurately inspects GET /api/tags and
    correctly reports 'connected' when llama3.2:3b is available.
    """
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3.2:3b", "model": "llama3.2:3b"},
            {"name": "nomic-embed-text:latest", "model": "nomic-embed-text:latest"},
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        health = await provider.check_health()
        assert health.name == "ollama"
        assert health.configured is True
        assert health.status == "connected"
        assert health.model == "llama3.2:3b"
        assert "llama3.2:3b" in health.available_models
        assert "nomic-embed-text:latest" in health.available_models
        assert "2 model(s) installed" in (health.detail or "")


def test_session_create_defaults_to_configured_ollama_provider():
    """
    Test that creating a new session via POST /api/sessions without specifying
    a provider defaults to the configured DEFAULT_MODEL_PROVIDER ('ollama').
    """
    response = client.post("/api/sessions", json={"title": "Test Ollama Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["model_provider"] == "ollama"
    assert data["title"] == "Test Ollama Session"
