import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


def get_utc_now() -> datetime:
    """Helper to return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base Declarative Class for all SQLAlchemy models."""
    pass


class SessionModel(Base):
    """
    Session entity representing an independent conversation thread.
    """
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"session-{uuid.uuid4()}",
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New Chat", nullable=False)
    model_provider: Mapped[str] = mapped_column(String(50), default="anthropic", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False
    )

    # Relationships
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at"
    )
    artifacts: Mapped[List["ArtifactModel"]] = relationship(
        "ArtifactModel",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        msg_count = len(self.messages) if "messages" in self.__dict__ and self.messages else 0
        return {
            "id": self.id,
            "title": self.title,
            "model_provider": self.model_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": msg_count,
        }


class MessageModel(Base):
    """
    Message entity storing individual turns within a session.
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"msg-{uuid.uuid4()}",
        index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sources_metadata: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="messages")
    citations: Mapped[List["CitationModel"]] = relationship(
        "CitationModel",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    artifacts: Mapped[List["ArtifactModel"]] = relationship(
        "ArtifactModel",
        back_populates="message",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        art_id = None
        art_title = None
        art_type = None
        if "artifacts" in self.__dict__ and self.artifacts:
            art = self.artifacts[0]
            art_id = art.id
            art_title = art.title
            art_type = art.artifact_type

        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "provider": self.provider,
            "sources": self.sources_metadata or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "artifact_id": art_id,
            "artifact_title": art_title,
            "artifact_type": art_type,
        }


class TranscriptModel(Base):
    """
    Transcript entity representing an entire podcast episode or newsletter article.
    """
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"transcript-{uuid.uuid4()}",
        index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repo_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    publish_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False
    )

    # Relationships
    chunks: Mapped[List["TranscriptChunkModel"]] = relationship(
        "TranscriptChunkModel",
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptChunkModel.chunk_index"
    )


class TranscriptChunkModel(Base):
    """
    Chunk entity representing segmented passages with optional dense vector embeddings.
    """
    __tablename__ = "transcript_chunks"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"chunk-{uuid.uuid4()}",
        index=True
    )
    transcript_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_start: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timestamp_end: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector embedding column (pgvector 768 dimensions for nomic-embed-text, nullable for non-vector environments)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(768), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    transcript: Mapped["TranscriptModel"] = relationship("TranscriptModel", back_populates="chunks")
    citations: Mapped[List["CitationModel"]] = relationship(
        "CitationModel",
        back_populates="chunk",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_transcript_chunks_transcript_index", "transcript_id", "chunk_index"),
    )


class ArtifactModel(Base):
    """
    Artifact entity representing generated Markdown strategy guides, HTML widgets, or Ship 30 essays.
    """
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"artifact-{uuid.uuid4()}",
        index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'markdown', 'html', 'essay'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_demonstration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="artifacts")
    message: Mapped[Optional["MessageModel"]] = relationship("MessageModel", back_populates="artifacts")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "type": self.artifact_type,
            "title": self.title,
            "content": self.content,
            "version": self.version,
            "is_demonstration": self.is_demonstration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CitationModel(Base):
    """
    Citation entity linking an assistant message to a specific source transcript chunk.
    """
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"cite-{uuid.uuid4()}",
        index=True
    )
    message_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("transcript_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    citation_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_timestamp_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    repo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    message: Mapped["MessageModel"] = relationship("MessageModel", back_populates="citations")
    chunk: Mapped[Optional["TranscriptChunkModel"]] = relationship("TranscriptChunkModel", back_populates="citations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "chunk_id": self.chunk_id,
            "index": self.citation_index,
            "excerpt": self.excerpt,
            "title": self.source_title,
            "guest": self.guest_name,
            "youtube_url": self.youtube_timestamp_url,
            "repo_path": self.repo_path,
        }
