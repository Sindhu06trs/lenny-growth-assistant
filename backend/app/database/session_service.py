import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.database.models import SessionModel, MessageModel, ArtifactModel, CitationModel
from app.core.logging_config import logger


class SessionService:
    """
    CRUD Service managing conversation sessions and message persistence in PostgreSQL.
    """

    @staticmethod
    async def get_or_create_session(
        db: AsyncSession,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        title: str = "New Chat"
    ) -> SessionModel:
        """
        Retrieves an existing session by ID or creates a new session.
        """
        if session_id:
            result = await db.execute(
                select(SessionModel)
                .where(SessionModel.id == session_id)
                .options(selectinload(SessionModel.messages))
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        # Create new session
        resolved_provider = provider or settings.DEFAULT_MODEL_PROVIDER
        new_id = session_id or f"session-{uuid.uuid4()}"
        new_session = SessionModel(
            id=new_id,
            title=title,
            model_provider=resolved_provider,
        )
        db.add(new_session)
        await db.flush()
        logger.info(f"Created new database session: {new_id} (provider={resolved_provider})")
        return new_session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[SessionModel]:
        """
        Retrieves a session by ID with loaded messages.
        """
        result = await db.execute(
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(selectinload(SessionModel.messages))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionModel]:
        """
        Lists all sessions ordered by updated_at descending.
        """
        result = await db.execute(
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .order_by(desc(SessionModel.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> bool:
        """
        Deletes a session and all its associated messages (cascade).
        """
        session = await SessionService.get_session(db, session_id)
        if not session:
            return False
        await db.delete(session)
        await db.flush()
        logger.info(f"Deleted database session: {session_id}")
        return True

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        sources_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> MessageModel:
        """
        Persists a single message within a session.
        """
        # Ensure session exists
        await SessionService.get_or_create_session(
            db,
            session_id=session_id,
            provider=provider or settings.DEFAULT_MODEL_PROVIDER,
        )

        message = MessageModel(
            id=f"msg-{uuid.uuid4()}",
            session_id=session_id,
            role=role,
            content=content,
            provider=provider,
            sources_metadata=sources_metadata or [],
        )
        db.add(message)
        await db.flush()
        return message

    @staticmethod
    async def get_session_messages(
        db: AsyncSession,
        session_id: str,
        limit: int = 100
    ) -> List[MessageModel]:
        """
        Retrieves message history for a specific session ordered chronologically with loaded artifacts.
        """
        result = await db.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .options(selectinload(MessageModel.artifacts))
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def save_artifact(
        db: AsyncSession,
        session_id: str,
        artifact_type: str,
        title: str,
        content: str,
        message_id: Optional[str] = None,
        is_demonstration: bool = False,
        version: int = 1,
    ) -> ArtifactModel:
        """
        Persists a generated artifact within a session.
        If an artifact for the given message_id already exists, updates and returns it to prevent duplicates.
        """
        if message_id:
            existing = await db.execute(
                select(ArtifactModel).where(ArtifactModel.message_id == message_id)
            )
            found = existing.scalar_one_or_none()
            if found:
                found.title = title
                found.content = content
                found.artifact_type = artifact_type
                found.version = version
                await db.flush()
                return found

        artifact = ArtifactModel(
            id=f"artifact-{uuid.uuid4()}",
            session_id=session_id,
            message_id=message_id,
            artifact_type=artifact_type,
            title=title,
            content=content,
            version=version,
            is_demonstration=is_demonstration,
        )
        db.add(artifact)
        await db.flush()
        return artifact

    @staticmethod
    async def get_artifact(
        db: AsyncSession,
        artifact_id: str
    ) -> Optional[ArtifactModel]:
        """
        Retrieves a single artifact by its ID.
        """
        result = await db.execute(
            select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_artifacts(
        db: AsyncSession,
        session_id: str
    ) -> List[ArtifactModel]:
        """
        Retrieves all artifacts belonging to a session ordered chronologically.
        """
        result = await db.execute(
            select(ArtifactModel)
            .where(ArtifactModel.session_id == session_id)
            .order_by(ArtifactModel.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def save_citations(
        db: AsyncSession,
        message_id: str,
        citations: List[Dict[str, Any]]
    ) -> List[CitationModel]:
        """
        Persists citation records linked to a specific assistant message.
        """
        saved_records = []
        for idx, cite in enumerate(citations, start=1):
            record = CitationModel(
                id=f"cite-{uuid.uuid4()}",
                message_id=message_id,
                chunk_id=cite.get("id") or cite.get("chunk_id"),
                citation_index=idx,
                excerpt=cite.get("excerpt", ""),
                source_title=cite.get("title", ""),
                guest_name=cite.get("guest", ""),
                youtube_timestamp_url=cite.get("youtube_url"),
                repo_path=cite.get("repo_path"),
            )
            db.add(record)
            saved_records.append(record)
        await db.flush()
        return saved_records

