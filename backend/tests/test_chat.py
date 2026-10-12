import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.llm.base import LLMResponse

client = TestClient(app)


def test_chat_valid_message_returns_honest_not_configured_status():
    """
    Test POST /api/chat with unconfigured provider returns 200 OK and honest not_configured status.
    Ensures no fake citations or simulated model responses are returned.
    """
    payload = {
        "message": "How can a startup improve customer retention?",
        "provider": "anthropic"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "not_configured"
    assert "session_id" in data
    assert data["session_id"].startswith("session-")
    assert "The Lenny Growth Assistant FastAPI backend" in data["message"]
    assert "sources" in data
    assert data["sources"] == []  # No fabricated sources
    assert "timestamp" in data
    assert data["provider"] == "anthropic"


def test_chat_defaults_to_ollama_provider():
    """
    Test POST /api/chat defaults to ollama provider when omitted from request.
    """
    payload = {
        "message": "What is cohort retention?"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "ollama"


def test_chat_preserves_custom_session_id():
    """
    Test POST /api/chat preserves caller-provided session_id.
    """
    custom_session = "custom-session-uuid-999"
    payload = {
        "message": "What is the PMF benchmark for B2B SaaS?",
        "session_id": custom_session
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["session_id"] == custom_session


def test_chat_preserves_provider_selection():
    """
    Test POST /api/chat preserves provider override.
    """
    payload = {
        "message": "Explain viral growth loops vs funnels.",
        "provider": "ollama"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["provider"] == "ollama"


def test_chat_rejects_empty_message():
    """
    Test POST /api/chat rejects empty message string with 422 Unprocessable Entity.
    """
    payload = {
        "message": ""
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert data["status_code"] == 422


def test_chat_rejects_whitespace_only_message():
    """
    Test POST /api/chat rejects whitespace-only string with 422 Unprocessable Entity.
    """
    payload = {
        "message": "   \n\t   "
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert data["status_code"] == 422


def test_chat_rejects_missing_message_field():
    """
    Test POST /api/chat rejects payload missing the required 'message' field.
    """
    payload = {
        "session_id": "session-123"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert data["status_code"] == 422


def test_chat_rejects_exceeded_max_length():
    """
    Test POST /api/chat rejects messages exceeding 4000 characters.
    """
    payload = {
        "message": "A" * 4001
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data


def test_chat_with_mocked_ollama_success():
    """
    Test POST /api/chat with provider='ollama' returns 200 OK and expected response text.
    """
    mock_provider = MagicMock()
    mock_provider.name = "ollama"
    mock_provider.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="PMF is when customers are pulling the product out of your hands.",
            provider="ollama",
            model="llama3.2:3b",
        )
    )

    with patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        payload = {
            "message": "What is PMF according to Marc Andreessen?",
            "provider": "ollama",
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["provider"] == "ollama"
        assert "pulling the product" in data["message"]
        assert "session_id" in data
        assert "timestamp" in data
