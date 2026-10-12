import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.core.embeddings import (
    BaseEmbeddingProvider,
    get_embedding_provider,
    EmbeddingProviderError,
    EmbeddingDimensionMismatchError,
)
from app.database.models import TranscriptModel, TranscriptChunkModel
from app.ingestion.parser import TranscriptParser
from app.ingestion.chunker import TranscriptChunker


@dataclass
class IngestionResult:
    """Summary of transcript ingestion execution."""
    status: str  # 'success', 'warning', 'error', 'no_documents_found'
    source_dir: str
    documents_found: int = 0
    documents_ingested: int = 0
    documents_skipped: int = 0
    chunks_created: int = 0
    chunks_embedded: int = 0
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class TranscriptIngestionPipeline:
    """
    Orchestrates reading transcript files, chunking, optional vector embedding,
    and duplicate-safe persistence to PostgreSQL and pgvector.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.chunker = TranscriptChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding_provider = embedding_provider

    async def ingest_directory(
        self,
        db: AsyncSession,
        source_dir: Path,
        generate_embeddings: bool = True,
        force_refresh: bool = False,
    ) -> IngestionResult:
        """
        Ingests all valid transcripts found within the specified directory.
        """
        source_path = Path(source_dir).resolve()
        result = IngestionResult(
            status="success",
            source_dir=str(source_path),
        )

        if not source_path.exists() or not source_path.is_dir():
            msg = f"Source transcript directory does not exist: {source_path}"
            logger.error(msg)
            result.status = "error"
            result.errors.append(msg)
            return result

        # Collect candidate transcript files (.md, .txt, .json)
        files = []
        for ext in ("*.md", "*.txt", "*.json"):
            files.extend(source_path.rglob(ext))

        # Filter out non-transcript files (README, license, index, etc.)
        valid_files = [
            f for f in files
            if f.is_file()
            and f.name.lower() not in ("readme.md", "license", "license.md", ".gitkeep")
            and "index" not in str(f.parent.name).lower()
        ]

        result.documents_found = len(valid_files)

        if not valid_files:
            msg = f"No transcript files found in directory: {source_path}"
            logger.warning(msg)
            result.status = "no_documents_found"
            result.errors.append(msg)
            return result

        logger.info(f"Found {len(valid_files)} transcript files in {source_path}. Starting ingestion...")

        # Initialize and validate embedding provider if embeddings requested
        embedder: Optional[BaseEmbeddingProvider] = self.embedding_provider
        if generate_embeddings and embedder is None:
            try:
                embedder = get_embedding_provider()
            except Exception as e:
                logger.warning(f"Could not initialize embedding provider: {e}. Ingesting without embeddings.")
                result.errors.append(f"Embeddings skipped: {str(e)}")

        if embedder and generate_embeddings:
            result.embedding_provider = embedder.provider_name
            result.embedding_model = embedder.model_name
            try:
                logger.info(f"Validating embedding dimension for {embedder.provider_name} ({embedder.model_name})...")
                await embedder.validate_dimension(expected_dim=settings.EMBEDDING_DIMENSION)
                logger.info(f"Embedding dimension verified: {settings.EMBEDDING_DIMENSION} dimensions.")
            except EmbeddingDimensionMismatchError as e:
                logger.error(f"Embedding dimension mismatch: {e.message}")
                result.status = "error"
                result.errors.append(e.message)
                return result
            except Exception as e:
                logger.warning(f"Embedding validation notice: {e}. Proceeding with cautious generation.")

        # Process each file
        for file_path in valid_files:
            try:
                parsed = TranscriptParser.parse_file(file_path, base_dir=source_path)
                if not parsed:
                    continue

                # Deterministic Transcript ID
                path_hash = hashlib.sha256(parsed.repo_path.encode("utf-8")).hexdigest()[:16]
                transcript_id = f"transcript-{path_hash}"

                # Check if document already exists
                existing_res = await db.execute(
                    select(TranscriptModel).where(
                        (TranscriptModel.id == transcript_id) | (TranscriptModel.file_sha256 == parsed.file_sha256)
                    )
                )
                existing_transcript = existing_res.scalar_one_or_none()

                if existing_transcript and not force_refresh:
                    # Check if chunks exist; if embeddings are requested, skip only if already embedded
                    if generate_embeddings:
                        chunk_embedded_res = await db.execute(
                            select(TranscriptChunkModel.id).where(
                                TranscriptChunkModel.transcript_id == existing_transcript.id,
                                TranscriptChunkModel.embedding.isnot(None),
                            )
                        )
                        if chunk_embedded_res.first() is not None:
                            logger.debug(f"Skipping already-embedded transcript: {parsed.title} ({parsed.repo_path})")
                            result.documents_skipped += 1
                            continue
                    else:
                        chunk_count_res = await db.execute(
                            select(TranscriptChunkModel.id).where(TranscriptChunkModel.transcript_id == existing_transcript.id)
                        )
                        if chunk_count_res.first() is not None:
                            logger.debug(f"Skipping unmodified transcript: {parsed.title} ({parsed.repo_path})")
                            result.documents_skipped += 1
                            continue

                # Create or update TranscriptModel
                if existing_transcript:
                    existing_transcript.title = parsed.title
                    existing_transcript.guest_name = parsed.guest_name
                    existing_transcript.repo_path = parsed.repo_path
                    existing_transcript.youtube_url = parsed.youtube_url
                    existing_transcript.video_id = parsed.video_id
                    existing_transcript.publish_date = parsed.publish_date
                    existing_transcript.description = parsed.description
                    existing_transcript.duration_seconds = parsed.duration_seconds
                    existing_transcript.file_sha256 = parsed.file_sha256
                    existing_transcript.extra_metadata = parsed.extra_metadata
                    transcript_record = existing_transcript
                    # Delete existing chunks for clean update
                    await db.execute(
                        delete(TranscriptChunkModel).where(TranscriptChunkModel.transcript_id == existing_transcript.id)
                    )
                else:
                    transcript_record = TranscriptModel(
                        id=transcript_id,
                        title=parsed.title,
                        guest_name=parsed.guest_name,
                        repo_path=parsed.repo_path,
                        youtube_url=parsed.youtube_url,
                        video_id=parsed.video_id,
                        publish_date=parsed.publish_date,
                        description=parsed.description,
                        duration_seconds=parsed.duration_seconds,
                        file_sha256=parsed.file_sha256,
                        extra_metadata=parsed.extra_metadata,
                    )
                    db.add(transcript_record)

                await db.flush()

                # Generate Chunks
                chunk_data_list = self.chunker.chunk_transcript(transcript_record.id, parsed)
                if not chunk_data_list:
                    logger.warning(f"No chunks generated for '{parsed.title}'")
                    continue

                # Generate Embeddings in Batches if enabled
                chunk_embeddings = [None] * len(chunk_data_list)
                if embedder and generate_embeddings:
                    try:
                        texts_to_embed = [c.content for c in chunk_data_list]
                        batch_size = 20
                        all_vectors = []
                        for i in range(0, len(texts_to_embed), batch_size):
                            batch = texts_to_embed[i : i + batch_size]
                            vectors = await embedder.embed_batch(batch)
                            all_vectors.extend(vectors)
                        chunk_embeddings = all_vectors
                        result.chunks_embedded += len(all_vectors)
                    except Exception as e:
                        logger.warning(f"Failed to generate embeddings for '{parsed.title}': {e}")
                        result.errors.append(f"Failed embedding chunks for {parsed.title}: {type(e).__name__}")

                # Save chunks to DB
                for idx, c in enumerate(chunk_data_list):
                    chunk_model = TranscriptChunkModel(
                        id=c.chunk_id,
                        transcript_id=transcript_record.id,
                        chunk_index=c.chunk_index,
                        timestamp_start=c.timestamp_start,
                        timestamp_end=c.timestamp_end,
                        content=c.content,
                        embedding=chunk_embeddings[idx] if idx < len(chunk_embeddings) else None,
                        extra_metadata=c.extra_metadata,
                    )
                    db.add(chunk_model)

                await db.flush()
                result.documents_ingested += 1
                result.chunks_created += len(chunk_data_list)
                logger.info(f"Ingested '{parsed.title}' ({len(chunk_data_list)} chunks)")

            except Exception as e:
                logger.error(f"Error ingesting file '{file_path}': {e}", exc_info=True)
                await db.rollback()
                result.errors.append(f"Error on {file_path.name}: {str(e)}")

        await db.commit()

        if result.documents_ingested == 0 and result.documents_skipped == 0:
            result.status = "warning"
            result.errors.append("No documents could be successfully parsed or ingested.")

        return result
