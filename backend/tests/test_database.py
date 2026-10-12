import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session_service import SessionService
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_create_and_retrieve_session(db_session: AsyncSession):
    """
    Test creating a new session and retrieving it by session_id.
    """
    session = await SessionService.get_or_create_session(
        db=db_session,
        session_id="test-session-100",
        provider="anthropic",
        title="PLG Growth Strategy"
    )
    assert session.id == "test-session-100"
    assert session.title == "PLG Growth Strategy"
    assert session.model_provider == "anthropic"
    assert session.created_at is not None

    retrieved = await SessionService.get_session(db_session, "test-session-100")
    assert retrieved is not None
    assert retrieved.id == "test-session-100"


@pytest.mark.asyncio
async def test_save_and_retrieve_messages(db_session: AsyncSession):
    """
    Test saving user and assistant messages and retrieving them in chronological order.
    """
    session_id = "test-session-200"
    await SessionService.get_or_create_session(db_session, session_id=session_id)

    msg1 = await SessionService.save_message(
        db=db_session,
        session_id=session_id,
        role="user",
        content="What is retention rate?",
        provider="anthropic"
    )
    msg2 = await SessionService.save_message(
        db=db_session,
        session_id=session_id,
        role="assistant",
        content="Retention is the percentage of active users who return.",
        provider="anthropic"
    )

    assert msg1.id.startswith("msg-")
    assert msg2.id.startswith("msg-")

    messages = await SessionService.get_session_messages(db_session, session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What is retention rate?"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_session_message_isolation(db_session: AsyncSession):
    """
    Test that messages from session A never bleed into session B.
    """
    session_a = "session-alpha"
    session_b = "session-beta"

    await SessionService.save_message(db_session, session_a, "user", "Message in Alpha")
    await SessionService.save_message(db_session, session_b, "user", "Message in Beta")

    messages_a = await SessionService.get_session_messages(db_session, session_a)
    messages_b = await SessionService.get_session_messages(db_session, session_b)

    assert len(messages_a) == 1
    assert messages_a[0].content == "Message in Alpha"
    assert len(messages_b) == 1
    assert messages_b[0].content == "Message in Beta"


@pytest.mark.asyncio
async def test_delete_session_cascades_messages(db_session: AsyncSession):
    """
    Test that deleting a session automatically deletes all its associated messages.
    """
    session_id = "session-to-delete"
    await SessionService.save_message(db_session, session_id, "user", "Will be deleted")

    deleted = await SessionService.delete_session(db_session, session_id)
    assert deleted is True

    retrieved = await SessionService.get_session(db_session, session_id)
    assert retrieved is None

    messages = await SessionService.get_session_messages(db_session, session_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_save_artifact(db_session: AsyncSession):
    """
    Test persisting an artifact linked to a session.
    """
    session_id = "session-with-artifact"
    artifact = await SessionService.save_artifact(
        db=db_session,
        session_id=session_id,
        artifact_type="html",
        title="Retention Calculator",
        content="<html><body>Demo</body></html>",
        is_demonstration=True
    )
    assert artifact.id.startswith("artifact-")
    assert artifact.artifact_type == "html"
    assert artifact.title == "Retention Calculator"
    assert artifact.is_demonstration is True


def test_sessions_api_crud_endpoints():
    """
    Test REST endpoints for Session creation, listing, and message retrieval.
    """
    # 1. Create a new session via API
    create_payload = {
        "title": "Pricing Strategy Session",
        "provider": "anthropic"
    }
    res_create = client.post("/api/sessions", json=create_payload)
    assert res_create.status_code == 201
    created_data = res_create.json()
    session_id = created_data["id"]
    assert created_data["title"] == "Pricing Strategy Session"

    # 2. List sessions
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    sessions_list = res_list.json()
    assert any(s["id"] == session_id for s in sessions_list)

    # 3. Post a message to this session via chat endpoint
    chat_payload = {
        "message": "How do we price a self-serve SaaS product?",
        "session_id": session_id
    }
    res_chat = client.post("/api/chat", json=chat_payload)
    assert res_chat.status_code == 200
    assert res_chat.json()["session_id"] == session_id

    # 4. Retrieve messages for the session
    res_msgs = client.get(f"/api/sessions/{session_id}/messages")
    assert res_msgs.status_code == 200
    messages = res_msgs.json()
    assert len(messages) == 2  # User query + Assistant response
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "How do we price a self-serve SaaS product?"
    assert messages[1]["role"] == "assistant"

    # 5. Delete session
    res_del = client.delete(f"/api/sessions/{session_id}")
    assert res_del.status_code == 204


def test_health_db_endpoint():
    """
    Test GET /health/db endpoint returns connectivity information.
    """
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
