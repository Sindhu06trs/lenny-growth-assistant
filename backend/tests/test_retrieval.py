import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TranscriptModel, TranscriptChunkModel
from app.retrieval.service import RetrievalService, RetrievedChunk, compute_cosine_similarity


def test_cosine_similarity_math():
    # Identical vectors -> 1.0
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v2), 0.001) == 1.0

    # Orthogonal vectors -> 0.0
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v3), 0.001) == 0.0

    # Opposite vectors -> -1.0
    v4 = [-1.0, 0.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v4), 0.001) == -1.0


@pytest.mark.asyncio
async def test_retrieval_empty_database_returns_empty_list(db_session: AsyncSession):
    count = await RetrievalService.get_indexed_chunk_count(db_session)
    assert count == 0

    query_vec = [0.1] * 768
    results = await RetrievalService.search_similar_chunks(db_session, query_vec, top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_retrieval_with_chunks_and_thresholding(db_session: AsyncSession):
    # 1. Seed transcript
    transcript = TranscriptModel(
        id="t-brian-chesky",
        title="Brian Chesky's new playbook",
        guest_name="Brian Chesky",
        repo_path="brian-chesky/transcript.md",
        youtube_url="https://www.youtube.com/watch?v=4ef0juAMqoE",
    )
    db_session.add(transcript)

    # Vector A: very close to query (768 dimensions)
    vec_a = [1.0] + [0.0] * 767
    # Vector B: somewhat close
    vec_b = [0.707, 0.707] + [0.0] * 766
    # Vector C: orthogonal / far
    vec_c = [0.0, 1.0] + [0.0] * 766

    chunk_a = TranscriptChunkModel(
        id="c-001",
        transcript_id="t-brian-chesky",
        chunk_index=0,
        content="Clarity is what everyone really wants. Leaders are in the details.",
        timestamp_start="00:00:15",
        embedding=vec_a,
    )
    chunk_b = TranscriptChunkModel(
        id="c-002",
        transcript_id="t-brian-chesky",
        chunk_index=1,
        content="We don't have traditional PMs. We combined inbound PM with outbound PMM.",
        timestamp_start="00:06:46",
        embedding=vec_b,
    )
    chunk_c = TranscriptChunkModel(
        id="c-003",
        transcript_id="t-brian-chesky",
        chunk_index=2,
        content="Performance marketing is like a laser, brand marketing is a chandelier.",
        timestamp_start="00:12:17",
        embedding=vec_c,
    )
    db_session.add_all([chunk_a, chunk_b, chunk_c])
    await db_session.commit()

    query_vec = [1.0] + [0.0] * 767

    # Test top_k=2 with threshold=0.5
    results = await RetrievalService.search_similar_chunks(
        db_session,
        query_embedding=query_vec,
        top_k=2,
        similarity_threshold=0.5,
    )

    assert len(results) == 2
    assert results[0].id == "c-001"
    assert results[0].guest_name == "Brian Chesky"
    assert results[0].similarity > 0.99
    assert results[0].youtube_timestamp_url == "https://www.youtube.com/watch?v=4ef0juAMqoE&t=15s"

    assert results[1].id == "c-002"
    assert results[1].similarity > 0.7

    # Test high threshold (0.8) excludes chunk_b
    high_thresh_results = await RetrievalService.search_similar_chunks(
        db_session,
        query_embedding=query_vec,
        top_k=5,
        similarity_threshold=0.8,
    )
    assert len(high_thresh_results) == 1
    assert high_thresh_results[0].id == "c-001"


@pytest.mark.asyncio
async def test_retrieval_guest_filtering(db_session: AsyncSession):
    t1 = TranscriptModel(
        id="t-brian",
        title="Brian Chesky Episode",
        guest_name="Brian Chesky",
        repo_path="brian/transcript.md",
    )
    t2 = TranscriptModel(
        id="t-shreyas",
        title="Shreyas Doshi Episode",
        guest_name="Shreyas Doshi",
        repo_path="shreyas/transcript.md",
    )
    db_session.add_all([t1, t2])

    target_vec = [1.0] + [0.0] * 767

    c1 = TranscriptChunkModel(
        id="c-brian-1",
        transcript_id="t-brian",
        chunk_index=0,
        content="Design and PM integration.",
        embedding=target_vec,
    )
    c2 = TranscriptChunkModel(
        id="c-shreyas-1",
        transcript_id="t-shreyas",
        chunk_index=0,
        content="Pre-mortems and product leadership.",
        embedding=target_vec,
    )
    db_session.add_all([c1, c2])
    await db_session.commit()

    # Query with guest filter
    res = await RetrievalService.search_similar_chunks(
        db_session,
        query_embedding=target_vec,
        top_k=5,
        similarity_threshold=0.5,
        guest_filter="Shreyas",
    )
    assert len(res) == 1
    assert res[0].guest_name == "Shreyas Doshi"
    assert res[0].id == "c-shreyas-1"
