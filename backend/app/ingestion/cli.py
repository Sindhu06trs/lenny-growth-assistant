import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select, func
from app.core.config import settings
from app.core.logging_config import logger
from app.database.connection import get_async_session_context
from app.database.models import TranscriptModel, TranscriptChunkModel
from app.core.embeddings import get_embedding_provider
from app.ingestion.pipeline import TranscriptIngestionPipeline


async def verify_database_transcripts():
    """Prints current database statistics for transcripts and chunks."""
    async with get_async_session_context() as session:
        t_count_res = await session.execute(select(func.count(TranscriptModel.id)))
        t_count = t_count_res.scalar() or 0

        c_count_res = await session.execute(select(func.count(TranscriptChunkModel.id)))
        c_count = c_count_res.scalar() or 0

        embedded_res = await session.execute(
            select(func.count(TranscriptChunkModel.id)).where(TranscriptChunkModel.embedding.isnot(None))
        )
        embedded_count = embedded_res.scalar() or 0

        print("\n" + "=" * 60)
        print("[STATUS] PGVECTOR TRANSCRIPT DATABASE STATUS")
        print("=" * 60)
        print(f"Total Transcript Documents: {t_count}")
        print(f"Total Chunks:               {c_count}")
        print(f"Chunks with Embeddings:     {embedded_count}")
        print("=" * 60 + "\n")


async def run_cli():
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast transcripts into PostgreSQL & pgvector.")
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=settings.TRANSCRIPT_DATA_DIR,
        help="Path to directory containing transcripts (default: ./data/raw or ./data/samples)",
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="Skip embedding generation (ingest documents and chunks as text only)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Embedding provider override ('openai' or 'ollama')",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-ingest all documents even if SHA256 has not changed",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify and display transcript count in PostgreSQL without ingesting",
    )

    args = parser.parse_args()

    if args.verify:
        await verify_database_transcripts()
        return

    source_path = Path(args.source)
    if not source_path.exists():
        # Fallback to data/samples if default ./data/raw is empty or missing
        samples_path = Path("./data/samples")
        if samples_path.exists():
            print(f"Source path '{source_path}' not found. Falling back to '{samples_path}'...")
            source_path = samples_path
        else:
            print(f"[ERROR] Source directory '{source_path}' does not exist.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("THE LENNY GROWTH ASSISTANT -- TRANSCRIPT INGESTION")
    print("=" * 60)
    print(f"Source Directory:       {source_path.resolve()}")
    print(f"Embedding Provider:     {args.provider or settings.EMBEDDING_PROVIDER}")
    print(f"Embeddings Enabled:     {not args.no_embed}")
    print(f"Force Refresh:          {args.force}")
    print("=" * 60 + "\n")

    embedder = None
    if not args.no_embed:
        try:
            embedder = get_embedding_provider(args.provider)
            print(f"Initialized embedding provider: {embedder.provider_name} ({embedder.model_name})")
        except Exception as e:
            print(f"[NOTICE] Embedding provider notice: {e}")
            print("Proceeding with text-only ingestion...")

    pipeline = TranscriptIngestionPipeline(embedding_provider=embedder)

    async with get_async_session_context() as session:
        result = await pipeline.ingest_directory(
            db=session,
            source_dir=source_path,
            generate_embeddings=(not args.no_embed),
            force_refresh=args.force,
        )

    print("\n" + "=" * 60)
    print("[SUMMARY] INGESTION RESULT SUMMARY")
    print("=" * 60)
    print(f"Status:                 {result.status.upper()}")
    print(f"Documents Found:        {result.documents_found}")
    print(f"Documents Ingested:     {result.documents_ingested}")
    print(f"Documents Skipped:      {result.documents_skipped}")
    print(f"Chunks Created:         {result.chunks_created}")
    print(f"Chunks with Embeddings: {result.chunks_embedded}")
    if result.errors:
        print("\nWarnings/Errors:")
        for err in result.errors:
            print(f"  - {err}")
    print("=" * 60 + "\n")

    # Final DB check
    await verify_database_transcripts()


def main():
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
