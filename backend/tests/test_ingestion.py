import tempfile
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.parser import TranscriptParser, ParsedTranscript, parse_timestamp_seconds, format_youtube_timestamp_url
from app.ingestion.chunker import TranscriptChunker
from app.ingestion.pipeline import TranscriptIngestionPipeline


def test_parse_timestamp_seconds():
    assert parse_timestamp_seconds("00:01:27") == 87
    assert parse_timestamp_seconds("01:13:28") == 4408
    assert parse_timestamp_seconds("05:04") == 304
    assert parse_timestamp_seconds(None) is None
    assert parse_timestamp_seconds("invalid") is None


def test_format_youtube_timestamp_url():
    url = "https://www.youtube.com/watch?v=4ef0juAMqoE"
    formatted = format_youtube_timestamp_url(url, "00:01:27")
    assert formatted == "https://www.youtube.com/watch?v=4ef0juAMqoE&t=87s"
    assert format_youtube_timestamp_url(None, "00:01:27") is None
    assert format_youtube_timestamp_url(url, None) == url


def test_parser_markdown_with_frontmatter():
    content = """---
guest: Brian Chesky
title: Brian Chesky's new playbook
youtube_url: https://www.youtube.com/watch?v=4ef0juAMqoE
video_id: 4ef0juAMqoE
publish_date: 2023-11-12
duration_seconds: 4408
keywords:
  - product
  - growth
---

# Brian Chesky's new playbook

## Transcript

Brian Chesky (00:00:00):
Clarity is what everyone really wants. Leaders are in the details.

Lenny (00:01:01):
Today my guest is Brian Chesky. Welcome Brian!
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "transcript.md"
        file_path.write_text(content, encoding="utf-8")

        parsed = TranscriptParser.parse_file(file_path, base_dir=Path(tmp_dir))
        assert parsed is not None
        assert parsed.guest_name == "Brian Chesky"
        assert parsed.title == "Brian Chesky's new playbook"
        assert parsed.video_id == "4ef0juAMqoE"
        assert parsed.duration_seconds == 4408
        assert parsed.publish_date is not None
        assert len(parsed.utterances) >= 2
        assert parsed.utterances[0]["speaker"] == "Brian Chesky"
        assert parsed.utterances[0]["timestamp"] == "00:00:00"


def test_parser_handles_empty_and_malformed_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Empty file
        empty_file = Path(tmp_dir) / "empty.md"
        empty_file.write_text("", encoding="utf-8")
        assert TranscriptParser.parse_file(empty_file) is None

        # 2. Whitespace only
        ws_file = Path(tmp_dir) / "whitespace.txt"
        ws_file.write_text("   \n\n  \t ", encoding="utf-8")
        assert TranscriptParser.parse_file(ws_file) is None

        # 3. Malformed YAML frontmatter
        bad_yaml = Path(tmp_dir) / "bad_yaml.md"
        bad_yaml.write_text("---\n[invalid yaml: : : : \n---\nBody content here.", encoding="utf-8")
        parsed = TranscriptParser.parse_file(bad_yaml)
        assert parsed is not None
        assert "Body content here." in parsed.content

        # 4. Non-existent file
        missing_file = Path(tmp_dir) / "does_not_exist.md"
        assert TranscriptParser.parse_file(missing_file) is None


def test_chunker_sliding_window_and_metadata_preservation():
    parsed = ParsedTranscript(
        title="Test Episode",
        guest_name="Elena Verna",
        repo_path="elena-verna/transcript.md",
        file_sha256="abc123sha",
        content="Product-led growth framework.",
        utterances=[
            {"speaker": "Lenny", "timestamp": "00:00:10", "text": "Welcome Elena. How do you define PLG?"},
            {"speaker": "Elena Verna", "timestamp": "00:00:25", "text": "PLG is an organizational alignment where the product drives acquisition, retention, and monetization."},
            {"speaker": "Lenny", "timestamp": "00:01:05", "text": "What is the biggest pitfall companies face?"},
            {"speaker": "Elena Verna", "timestamp": "00:01:20", "text": "Thinking that PLG means not having a sales team. Modern B2B needs product-led sales."},
        ]
    )

    chunker = TranscriptChunker(chunk_size=200, chunk_overlap=50, min_chunk_length=30)
    chunks = chunker.chunk_transcript("transcript-test01", parsed)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.chunk_id.startswith("transcript-test01-c")
        assert c.content
        assert c.extra_metadata.get("guest") == "Elena Verna"
        assert "speakers" in c.extra_metadata


@pytest.mark.asyncio
async def test_pipeline_missing_directory_returns_error(db_session: AsyncSession):
    pipeline = TranscriptIngestionPipeline()
    fake_dir = Path("C:/definitely/non_existent_transcript_dir_12345")
    result = await pipeline.ingest_directory(db_session, fake_dir, generate_embeddings=False)

    assert result.status == "error"
    assert result.documents_found == 0
    assert result.documents_ingested == 0
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_pipeline_duplicate_safe_ingestion(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test_ep.md"
        test_file.write_text(
            """---
guest: Shreyas Doshi
title: The Art of Product Management
youtube_url: https://www.youtube.com/watch?v=YP_QghPLG-8
---
Shreyas Doshi (00:00:00):
Pre-mortems prevent ugly post-mortems. Always simulate the future failure.
""",
            encoding="utf-8"
        )

        pipeline = TranscriptIngestionPipeline()

        # Run 1: Ingest
        res1 = await pipeline.ingest_directory(db_session, Path(tmp_dir), generate_embeddings=False)
        assert res1.status == "success"
        assert res1.documents_ingested == 1
        assert res1.documents_skipped == 0
        assert res1.chunks_created > 0

        # Run 2: Re-ingest exact same file without force
        res2 = await pipeline.ingest_directory(db_session, Path(tmp_dir), generate_embeddings=False, force_refresh=False)
        assert res2.status == "success"
        assert res2.documents_ingested == 0
        assert res2.documents_skipped == 1
        assert res2.chunks_created == 0


@pytest.mark.asyncio
async def test_pipeline_with_mocked_ollama_embeddings_and_force_refresh(db_session: AsyncSession):
    from unittest.mock import AsyncMock, MagicMock
    from app.core.embeddings import BaseEmbeddingProvider
    from app.database.models import TranscriptModel, TranscriptChunkModel
    from sqlalchemy import select

    mock_embedder = MagicMock(spec=BaseEmbeddingProvider)
    mock_embedder.provider_name = "ollama"
    mock_embedder.model_name = "nomic-embed-text"
    mock_embedder.expected_dimension = 768
    mock_embedder.validate_dimension = AsyncMock(return_value=None)
    mock_embedder.embed_batch = AsyncMock(side_effect=lambda texts: [[0.05] * 768 for _ in texts])

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test_ollama_ep.md"
        test_file.write_text(
            """---
guest: Julie Zhuo
title: The Making of a Manager
youtube_url: https://www.youtube.com/watch?v=julie123
---
Julie Zhuo (00:00:00):
Management is fundamentally about achieving better outcomes together with a group of people. Your job as a manager is to get better outcomes from a group of people working together.

Lenny (00:01:00):
What is the biggest shift when moving from an Individual Contributor to a Manager?
""",
            encoding="utf-8"
        )

        pipeline = TranscriptIngestionPipeline(embedding_provider=mock_embedder)

        # 1. Initial ingestion with embeddings
        res1 = await pipeline.ingest_directory(db_session, Path(tmp_dir), generate_embeddings=True)
        assert res1.status == "success"
        assert res1.documents_ingested == 1
        assert res1.chunks_embedded > 0

        # Verify chunks have 768-dim embeddings in DB
        chunks_res = await db_session.execute(select(TranscriptChunkModel))
        chunks = chunks_res.scalars().all()
        assert len(chunks) == res1.chunks_created
        for c in chunks:
            assert c.embedding is not None
            assert len(c.embedding) == 768

        initial_chunk_count = len(chunks)

        # 2. Re-ingest with force_refresh=True to verify zero duplicate records are created
        res2 = await pipeline.ingest_directory(db_session, Path(tmp_dir), generate_embeddings=True, force_refresh=True)
        assert res2.status == "success"
        assert res2.documents_ingested == 1

        # Confirm count in database is still exactly initial_chunk_count (no duplicates)
        chunks_after_res = await db_session.execute(select(TranscriptChunkModel))
        chunks_after = chunks_after_res.scalars().all()
        assert len(chunks_after) == initial_chunk_count
        for c in chunks_after:
            assert c.embedding is not None
            assert len(c.embedding) == 768
