from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database.models import TranscriptModel, TranscriptChunkModel, MessageModel, CitationModel
from app.api.routes.chat import build_rag_system_prompt
from app.retrieval.service import RetrievedChunk
from app.core.llm.base import LLMResponse


def test_build_rag_system_prompt_empty_database():
    prompt = build_rag_system_prompt([], database_has_transcripts=False)
    assert "No podcast transcripts have been indexed" in prompt
    assert "CLI: `python -m app.ingestion.cli" in prompt
    assert "Do not invent or fabricate quotes" in prompt


def test_build_rag_system_prompt_no_relevant_evidence():
    prompt = build_rag_system_prompt([], database_has_transcripts=True)
    assert "TRANSCRIPT SEARCH STATUS" in prompt
    assert "no podcast excerpts met the relevance similarity threshold" in prompt
    assert "Do not invent quotes" in prompt


def test_build_rag_system_prompt_with_retrieved_chunks():
    chunks = [
        RetrievedChunk(
            id="c-1",
            transcript_id="t-1",
            chunk_index=0,
            title="Brian Chesky's new playbook",
            guest_name="Brian Chesky",
            content="We combined inbound PM with outbound PMM.",
            similarity=0.92,
            timestamp_start="00:06:46",
            youtube_url="https://www.youtube.com/watch?v=4ef0juAMqoE",
        )
    ]
    prompt = build_rag_system_prompt(chunks, database_has_transcripts=True)
    assert "[EXCERPT 1]" in prompt
    assert "Episode: Brian Chesky's new playbook" in prompt
    assert "Guest: Brian Chesky" in prompt
    assert "00:06:46" in prompt
    assert "STRICT GROUNDING INSTRUCTIONS" in prompt


@pytest.mark.asyncio
async def test_chat_endpoint_returns_genuine_rag_citations(db_session: AsyncSession):
    # 1. Seed transcript and chunk
    t = TranscriptModel(
        id="t-pmf",
        title="Finding Product Market Fit",
        guest_name="Andy Rachleff",
        repo_path="andy-rachleff/transcript.md",
        youtube_url="https://www.youtube.com/watch?v=mock123",
    )
    c = TranscriptChunkModel(
        id="c-pmf-1",
        transcript_id="t-pmf",
        chunk_index=0,
        content="First you need product market fit, then you scale marketing.",
        timestamp_start="00:04:12",
        embedding=[0.5] * 768,
    )
    db_session.add_all([t, c])
    await db_session.commit()

    # 2. Mock embedding provider returning same vector
    mock_embedder = MagicMock()
    mock_embedder.embed_text = AsyncMock(return_value=[0.5] * 768)

    # 3. Mock LLM provider
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="According to Andy Rachleff, first you need PMF before scaling marketing.",
            provider="anthropic",
            model="claude-3-5-sonnet",
        )
    )

    with patch("app.api.routes.chat.get_embedding_provider", return_value=mock_embedder), \
         patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/chat",
                json={
                    "message": "When should a startup scale marketing according to Andy Rachleff?",
                    "session_id": "session-rag-test",
                    "provider": "anthropic",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["sources"]) == 1

        citation = data["sources"][0]
        assert citation["id"] == "c-pmf-1"
        assert citation["title"] == "Finding Product Market Fit"
        assert citation["guest"] == "Andy Rachleff"
        assert citation["timestamp"] == "00:04:12"
        assert "t=252s" in citation["youtube_url"]

        # 4. Verify citations persisted to database
        cites_res = await db_session.execute(select(CitationModel))
        cites_in_db = cites_res.scalars().all()
        assert len(cites_in_db) == 1
        assert cites_in_db[0].chunk_id == "c-pmf-1"
        assert cites_in_db[0].guest_name == "Andy Rachleff"


@pytest.mark.asyncio
async def test_chat_endpoint_safe_handling_when_embedding_fails(db_session: AsyncSession):
    # Seed a transcript so indexed_count > 0
    t = TranscriptModel(id="t-1", title="Title", guest_name="Guest", repo_path="p")
    c = TranscriptChunkModel(id="c-1", transcript_id="t-1", chunk_index=0, content="txt", embedding=[0.1]*768)
    db_session.add_all([t, c])
    await db_session.commit()

    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(
        return_value=LLMResponse(text="General advice", provider="anthropic", model="m")
    )

    # Embedding provider raises an error
    mock_embedder = MagicMock()
    mock_embedder.embed_text = AsyncMock(side_effect=Exception("Embedding connection failed"))

    with patch("app.api.routes.chat.get_embedding_provider", return_value=mock_embedder), \
         patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/chat",
                json={"message": "What is retention?", "provider": "anthropic"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        # Zero fabricated citations when retrieval failed
        assert data["sources"] == []


@pytest.mark.asyncio
async def test_ollama_rag_chat_integration(db_session: AsyncSession):
    """
    Test end-to-end RAG chat integration when provider='ollama':
    Retrieves pgvector chunks, injects verified excerpts into Ollama system prompt,
    generates response using llama3.2:3b, and attaches source citations.
    """
    t = TranscriptModel(
        id="t-chesky",
        title="Brian Chesky's new playbook",
        guest_name="Brian Chesky",
        repo_path="brian-chesky/transcript.md",
        youtube_url="https://www.youtube.com/watch?v=4ef0juAMqoE",
    )
    c = TranscriptChunkModel(
        id="c-chesky-1",
        transcript_id="t-chesky",
        chunk_index=0,
        content="We got rid of the classic product management function and combined it with product marketing.",
        timestamp_start="00:06:46",
        embedding=[0.4] * 768,
    )
    db_session.add_all([t, c])
    await db_session.commit()

    mock_embedder = MagicMock()
    mock_embedder.embed_text = AsyncMock(return_value=[0.4] * 768)

    mock_ollama = MagicMock()
    mock_ollama.generate_response = AsyncMock(
        return_value=LLMResponse(
            text="Brian Chesky explained that Airbnb combined product management with product marketing.",
            provider="ollama",
            model="llama3.2:3b",
        )
    )

    with patch("app.api.routes.chat.get_embedding_provider", return_value=mock_embedder), \
         patch("app.api.routes.chat.get_llm_provider", return_value=mock_ollama):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/chat",
                json={
                    "message": "What did Brian Chesky say about product management?",
                    "session_id": "session-ollama-rag",
                    "provider": "ollama",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["provider"] == "ollama"
        assert len(data["sources"]) == 1

        citation = data["sources"][0]
        assert citation["id"] == "c-chesky-1"
        assert citation["title"] == "Brian Chesky's new playbook"
        assert citation["guest"] == "Brian Chesky"
        assert citation["timestamp"] == "00:06:46"
        assert "t=406s" in citation["youtube_url"]

        # Verify system prompt passed to Ollama includes the excerpt
        call_args = mock_ollama.generate_response.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")
        assert "Brian Chesky's new playbook" in system_prompt
        assert "combined it with product marketing" in system_prompt


@pytest.mark.asyncio
async def test_ollama_rag_multi_turn_session_history(db_session: AsyncSession):
    """
    Test that Ollama chat responses retain and forward session conversation
    history across sequential multi-turn user interactions.
    """
    mock_embedder = MagicMock()
    mock_embedder.embed_text = AsyncMock(return_value=[0.1] * 768)

    mock_ollama = MagicMock()
    mock_ollama.generate_response = AsyncMock(
        side_effect=[
            LLMResponse(text="Turn 1 answer about product marketing.", provider="ollama", model="llama3.2:3b"),
            LLMResponse(text="Turn 2 answer with deeper context.", provider="ollama", model="llama3.2:3b"),
        ]
    )

    with patch("app.api.routes.chat.get_embedding_provider", return_value=mock_embedder), \
         patch("app.api.routes.chat.get_llm_provider", return_value=mock_ollama):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            session_id = "session-multi-turn-ollama"

            # Turn 1
            resp1 = await ac.post(
                "/api/chat",
                json={
                    "message": "First question: What is PMM?",
                    "session_id": session_id,
                    "provider": "ollama",
                },
            )
            assert resp1.status_code == 200
            assert resp1.json()["status"] == "success"

            # Turn 2
            resp2 = await ac.post(
                "/api/chat",
                json={
                    "message": "Second question: Can you give an example?",
                    "session_id": session_id,
                    "provider": "ollama",
                },
            )
            assert resp2.status_code == 200
            assert resp2.json()["status"] == "success"

        # Verify that turn 2 received the prior turns in messages payload
        call_args_2 = mock_ollama.generate_response.call_args_list[1]
        passed_messages = call_args_2.kwargs.get("messages", [])
        roles = [m["role"] for m in passed_messages]
        contents = [m["content"] for m in passed_messages]

        assert "user" in roles
        assert "assistant" in roles
        assert any("First question: What is PMM?" in c for c in contents)
        assert any("Turn 1 answer about product marketing." in c for c in contents)
        assert any("Second question: Can you give an example?" in c for c in contents)
