"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-10 17:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension (PostgreSQL only)
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create 'sessions' table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('model_provider', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)

    # 3. Create 'messages' table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('sources_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_session_id'), 'messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)

    # 4. Create 'transcripts' table
    op.create_table(
        'transcripts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('guest_name', sa.String(length=255), nullable=False),
        sa.Column('repo_path', sa.String(length=500), nullable=False),
        sa.Column('youtube_url', sa.String(length=500), nullable=True),
        sa.Column('video_id', sa.String(length=100), nullable=True),
        sa.Column('publish_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_sha256', sa.String(length=64), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcripts_id'), 'transcripts', ['id'], unique=False)
    op.create_index(op.f('ix_transcripts_guest_name'), 'transcripts', ['guest_name'], unique=False)
    op.create_index(op.f('ix_transcripts_repo_path'), 'transcripts', ['repo_path'], unique=False)
    op.create_index(op.f('ix_transcripts_video_id'), 'transcripts', ['video_id'], unique=False)
    op.create_index(op.f('ix_transcripts_file_sha256'), 'transcripts', ['file_sha256'], unique=False)

    # 5. Create 'transcript_chunks' table
    op.create_table(
        'transcript_chunks',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('transcript_id', sa.String(length=64), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('timestamp_start', sa.String(length=20), nullable=True),
        sa.Column('timestamp_end', sa.String(length=20), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_chunks_id'), 'transcript_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_transcript_chunks_transcript_id'), 'transcript_chunks', ['transcript_id'], unique=False)
    op.create_index('ix_transcript_chunks_transcript_index', 'transcript_chunks', ['transcript_id', 'chunk_index'], unique=False)

    # 6. Create 'artifacts' table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('message_id', sa.String(length=64), nullable=True),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_demonstration', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_id'), 'artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_artifacts_session_id'), 'artifacts', ['session_id'], unique=False)
    op.create_index(op.f('ix_artifacts_message_id'), 'artifacts', ['message_id'], unique=False)

    # 7. Create 'citations' table
    op.create_table(
        'citations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('message_id', sa.String(length=64), nullable=False),
        sa.Column('chunk_id', sa.String(length=64), nullable=True),
        sa.Column('citation_index', sa.Integer(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('source_title', sa.String(length=500), nullable=False),
        sa.Column('guest_name', sa.String(length=255), nullable=False),
        sa.Column('youtube_timestamp_url', sa.String(length=500), nullable=True),
        sa.Column('repo_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['transcript_chunks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_citations_id'), 'citations', ['id'], unique=False)
    op.create_index(op.f('ix_citations_message_id'), 'citations', ['message_id'], unique=False)
    op.create_index(op.f('ix_citations_chunk_id'), 'citations', ['chunk_id'], unique=False)


def downgrade() -> None:
    op.drop_table('citations')
    op.drop_table('artifacts')
    op.drop_table('transcript_chunks')
    op.drop_table('transcripts')
    op.drop_table('messages')
    op.drop_table('sessions')
