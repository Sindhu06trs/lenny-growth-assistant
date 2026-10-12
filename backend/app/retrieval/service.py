from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.database.models import TranscriptModel, TranscriptChunkModel
from app.ingestion.parser import format_youtube_timestamp_url


@dataclass
class RetrievedChunk:
    """Represents a matched transcript excerpt retrieved via pgvector search."""
    id: str
    transcript_id: str
    chunk_index: int
    title: str
    guest_name: str
    content: str
    similarity: float
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_timestamp_url: Optional[str] = None
    repo_path: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_citation_dict(self) -> Dict[str, Any]:
        """Converts into citation schema for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "guest": self.guest_name,
            "excerpt": self.content[:300] + "..." if len(self.content) > 300 else self.content,
            "timestamp": self.timestamp_start or "",
            "youtube_url": self.youtube_timestamp_url or self.youtube_url,
            "similarity": round(self.similarity, 3),
        }


import math

def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RetrievalService:
    """
    Executes cosine-similarity nearest-neighbor search over transcript chunk embeddings in PostgreSQL.
    """

    @staticmethod
    async def get_indexed_chunk_count(db: AsyncSession) -> int:
        """Returns the number of transcript chunks with non-null dense vector embeddings."""
        try:
            res = await db.execute(
                select(func.count(TranscriptChunkModel.id)).where(TranscriptChunkModel.embedding.isnot(None))
            )
            return res.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not check indexed chunk count: {e}")
            return 0

    @staticmethod
    async def get_total_transcript_count(db: AsyncSession) -> int:
        """Returns the total number of transcript documents stored in the database."""
        try:
            res = await db.execute(select(func.count(TranscriptModel.id)))
            return res.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not check transcript count: {e}")
            return 0

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        guest_filter: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieves the top-k most similar transcript chunks using pgvector cosine distance.
        """
        k = top_k or settings.RAG_TOP_K_CHUNKS
        threshold = similarity_threshold if similarity_threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

        if not query_embedding:
            return []

        # Validate that database has indexed chunks
        total_chunks = await RetrievalService.get_indexed_chunk_count(db)
        if total_chunks == 0:
            logger.debug("pgvector search called but 0 embedded chunks exist in the database.")
            return []

        # Check engine dialect: use Python similarity fallback if running on SQLite in unit tests
        bind = db.bind
        dialect_name = bind.dialect.name if bind else "postgresql"

        if dialect_name == "sqlite":
            # SQLite fallback for offline unit tests
            stmt = (
                select(TranscriptChunkModel, TranscriptModel)
                .join(TranscriptModel, TranscriptChunkModel.transcript_id == TranscriptModel.id)
                .where(TranscriptChunkModel.embedding.isnot(None))
            )
            if guest_filter:
                stmt = stmt.where(TranscriptModel.guest_name.ilike(f"%{guest_filter}%"))

            res = await db.execute(stmt)
            scored = []
            for chunk_row, trans_row in res.all():
                raw_emb = chunk_row.embedding
                if hasattr(raw_emb, "tolist"):
                    emb = raw_emb.tolist()
                elif isinstance(raw_emb, list):
                    emb = raw_emb
                elif isinstance(raw_emb, str):
                    try:
                        emb = [float(x.strip()) for x in raw_emb.strip("[]").split(",") if x.strip()]
                    except Exception:
                        continue
                elif hasattr(raw_emb, "__iter__"):
                    emb = list(raw_emb)
                else:
                    continue

                sim = compute_cosine_similarity(query_embedding, emb)
                if sim >= threshold:
                    scored.append((sim, chunk_row, trans_row))

            scored.sort(key=lambda x: x[0], reverse=True)
            retrieved = []
            for sim, chunk_row, trans_row in scored[:k]:
                yt_ts_url = format_youtube_timestamp_url(trans_row.youtube_url, chunk_row.timestamp_start)
                retrieved.append(
                    RetrievedChunk(
                        id=chunk_row.id,
                        transcript_id=chunk_row.transcript_id,
                        chunk_index=chunk_row.chunk_index,
                        title=trans_row.title,
                        guest_name=trans_row.guest_name,
                        content=chunk_row.content,
                        similarity=float(sim),
                        timestamp_start=chunk_row.timestamp_start,
                        timestamp_end=chunk_row.timestamp_end,
                        youtube_url=trans_row.youtube_url,
                        youtube_timestamp_url=yt_ts_url,
                        repo_path=trans_row.repo_path,
                        extra_metadata=chunk_row.extra_metadata or {},
                    )
                )
            return retrieved

        # Formulate SQL vector query using pgvector <=> (cosine distance) on PostgreSQL
        vector_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
        guest_clause = "AND LOWER(t.guest_name) LIKE LOWER(:guest)" if guest_filter else ""

        query_sql = text(f"""
            SELECT 
                tc.id,
                tc.transcript_id,
                tc.chunk_index,
                tc.timestamp_start,
                tc.timestamp_end,
                tc.content,
                tc.extra_metadata AS chunk_meta,
                t.title,
                t.guest_name,
                t.youtube_url,
                t.repo_path,
                1 - (tc.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM transcript_chunks tc
            JOIN transcripts t ON tc.transcript_id = t.id
            WHERE tc.embedding IS NOT NULL
              AND (1 - (tc.embedding <=> CAST(:query_vec AS vector))) >= :threshold
              {guest_clause}
            ORDER BY tc.embedding <=> CAST(:query_vec AS vector) ASC
            LIMIT :limit
        """)

        params: Dict[str, Any] = {
            "query_vec": vector_str,
            "threshold": threshold,
            "limit": k,
        }
        if guest_filter:
            params["guest"] = f"%{guest_filter}%"

        try:
            res = await db.execute(query_sql, params)
            rows = res.fetchall()

            retrieved: List[RetrievedChunk] = []
            for row in rows:
                yt_ts_url = format_youtube_timestamp_url(row.youtube_url, row.timestamp_start)
                retrieved.append(
                    RetrievedChunk(
                        id=row.id,
                        transcript_id=row.transcript_id,
                        chunk_index=row.chunk_index,
                        title=row.title,
                        guest_name=row.guest_name,
                        content=row.content,
                        similarity=float(row.similarity),
                        timestamp_start=row.timestamp_start,
                        timestamp_end=row.timestamp_end,
                        youtube_url=row.youtube_url,
                        youtube_timestamp_url=yt_ts_url,
                        repo_path=row.repo_path,
                        extra_metadata=row.chunk_meta or {},
                    )
                )

            logger.info(f"pgvector retrieved {len(retrieved)} chunks (top_k={k}, threshold={threshold})")
            return retrieved

        except Exception as e:
            logger.error(f"Error during pgvector similarity search: {e}", exc_info=True)
            return []
