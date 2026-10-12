import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.llm.base import LLMResponse
from app.api.routes.chat import detect_artifact_intent, extract_artifact_title
from app.database.session_service import SessionService
from app.database.models import SessionModel, MessageModel, ArtifactModel

client = TestClient(app)


def test_detect_artifact_intent_essays():
    assert detect_artifact_intent("Write an essay on user retention") == {"type": "essay", "category": "Ship 30 Atomic Essay"}
    assert detect_artifact_intent("Draft a Ship 30 essay about PMF") == {"type": "essay", "category": "Ship 30 Atomic Essay"}
    assert detect_artifact_intent("Create an atomic essay for early-stage founders") == {"type": "essay", "category": "Ship 30 Atomic Essay"}


def test_detect_artifact_intent_html():
    assert detect_artifact_intent("Create an html dashboard for churn") == {"type": "html", "category": "Interactive Tool"}
    assert detect_artifact_intent("Build an interactive calculator widget") == {"type": "html", "category": "Interactive Tool"}


def test_detect_artifact_intent_markdown_strategy():
    assert detect_artifact_intent("Generate a growth playbook for B2B SaaS") == {"type": "markdown", "category": "Strategy Guide"}
    assert detect_artifact_intent("Create a strategy guide on onboarding") == {"type": "markdown", "category": "Strategy Guide"}
    assert detect_artifact_intent("Provide this as an artifact") == {"type": "markdown", "category": "Strategy Guide"}


def test_detect_artifact_intent_normal_qa():
    assert detect_artifact_intent("What did Brian Chesky say about founder mode?") is None
    assert detect_artifact_intent("What is a good churn rate?") is None


def test_extract_artifact_title_from_heading():
    content = "# The Compounding Power of Retention\n\nMost founders focus on acquisition."
    assert extract_artifact_title(content, "retention essay") == "The Compounding Power of Retention"

    content_with_formatting = "# **Building Habit Loops in B2B SaaS**\n\nFramework details here."
    assert extract_artifact_title(content_with_formatting, "growth") == "Building Habit Loops in B2B SaaS"


def test_extract_artifact_title_fallback():
    content = "Most founders focus on acquisition instead of retention."
    assert extract_artifact_title(content, "write an essay on product retention") == "Product retention"


@pytest.mark.asyncio
async def test_get_artifact_endpoint_success(db_session):
    """
    Test GET /api/artifacts/{artifact_id} retrieves persisted artifact record.
    """
    session = SessionModel(id="test-session-art-1", title="Artifact Test", model_provider="ollama")
    db_session.add(session)
    await db_session.commit()

    artifact = await SessionService.save_artifact(
        db=db_session,
        session_id=session.id,
        artifact_type="essay",
        title="Why Cohort Retention Matters",
        content="# Why Cohort Retention Matters\n\nRetention is the foundation of growth.",
    )
    assert artifact is not None
    assert artifact.id is not None

    response = client.get(f"/api/artifacts/{artifact.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == artifact.id
    assert data["title"] == "Why Cohort Retention Matters"
    assert data["type"] == "essay"
    assert "Retention is the foundation" in data["content"]
    assert data["session_id"] == session.id
    assert data["version"] == 1
    assert data["is_demonstration"] is False


def test_get_artifact_endpoint_not_found():
    """
    Test GET /api/artifacts/{artifact_id} returns 404 for unknown ID.
    """
    response = client.get("/api/artifacts/nonexistent-artifact-999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_demo_artifact_endpoint_success():
    """
    Test GET /api/artifacts/demo-retention-calc returns the HTML demo artifact.
    """
    response = client.get("/api/artifacts/demo-retention-calc")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "demo-retention-calc"
    assert data["title"] == "Customer Retention & Cohort Simulator"
    assert data["type"] == "html"
    assert data["is_demonstration"] is True
    assert "SaaS Retention & ARR Simulator" in data["content"]


@pytest.mark.asyncio
async def test_list_session_artifacts(db_session):
    """
    Test GET /api/artifacts?session_id=... returns artifacts for the session.
    """
    session = SessionModel(id="test-session-list-art", title="List Test", model_provider="ollama")
    db_session.add(session)
    await db_session.commit()

    await SessionService.save_artifact(
        db=db_session,
        session_id=session.id,
        artifact_type="markdown",
        title="PLG Playbook",
        content="# PLG Playbook\nChecklist content.",
    )

    response = client.get(f"/api/artifacts?session_id={session.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "PLG Playbook"
    assert data[0]["type"] == "markdown"


def test_chat_creates_and_returns_artifact_record():
    """
    Test POST /api/chat with essay request generates content, creates Artifact record,
    and returns artifact metadata in ChatResponse.
    """
    mock_provider = MagicMock()
    mock_provider.name = "ollama"
    mock_provider.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="# The Leaky Bucket Paradox\n\nPouring water into a leaky bucket does not fix the holes.\n\n## 1. The Core Thesis\nFix retention first.",
            provider="ollama",
            model="llama3.2:3b",
        )
    )

    with patch("app.api.routes.chat.get_llm_provider", return_value=mock_provider):
        payload = {
            "message": "Write an atomic essay on why top-of-funnel fixes won't save a leaky bucket",
            "provider": "ollama",
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "artifact" in data
        assert data["artifact"] is not None
        assert data["artifact_id"] is not None

        art = data["artifact"]
        assert art["type"] == "essay"
        assert art["title"] == "The Leaky Bucket Paradox"
        assert "Pouring water into a leaky bucket" in art["content"]
        assert art["session_id"] == data["session_id"]

        # Fetch artifact from artifacts endpoint
        art_res = client.get(f"/api/artifacts/{data['artifact_id']}")
        assert art_res.status_code == 200
        saved_art = art_res.json()
        assert saved_art["id"] == art["id"]
        assert saved_art["title"] == "The Leaky Bucket Paradox"

        # Check session messages include artifact linkage
        msgs_res = client.get(f"/api/sessions/{data['session_id']}/messages")
        assert msgs_res.status_code == 200
        msgs = msgs_res.json()
        assistant_msgs = [m for m in msgs if m["role"] == "assistant"]
        assert len(assistant_msgs) >= 1
        assert assistant_msgs[0]["artifact_id"] == art["id"]
        assert assistant_msgs[0]["artifact_title"] == "The Leaky Bucket Paradox"
        assert assistant_msgs[0]["artifact_type"] == "essay"


@pytest.mark.asyncio
async def test_duplicate_prevention_on_same_message(db_session):
    """
    Test SessionService.save_artifact updates existing record rather than creating duplicates
    when called with the same message_id.
    """
    session = SessionModel(id="test-session-dup", title="Dup Test", model_provider="ollama")
    db_session.add(session)
    await db_session.flush()

    msg = MessageModel(id="msg-dup-1", session_id=session.id, role="assistant", content="Original content")
    db_session.add(msg)
    await db_session.commit()

    art1 = await SessionService.save_artifact(
        db=db_session,
        session_id=session.id,
        message_id=msg.id,
        artifact_type="essay",
        title="Original Essay",
        content="# Original Essay",
    )
    assert art1 is not None

    art2 = await SessionService.save_artifact(
        db=db_session,
        session_id=session.id,
        message_id=msg.id,
        artifact_type="essay",
        title="Updated Essay",
        content="# Updated Essay",
    )
    assert art2 is not None
    assert art2.id == art1.id  # Same record updated
    assert art2.title == "Updated Essay"

    all_arts = await SessionService.get_session_artifacts(db_session, session.id)
    assert len(all_arts) == 1
