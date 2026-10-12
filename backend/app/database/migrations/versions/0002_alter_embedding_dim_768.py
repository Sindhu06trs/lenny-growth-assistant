"""alter transcript_chunks embedding dimension to 768

Revision ID: 0002_alter_embedding_dim_768
Revises: 0001_initial_schema
Create Date: 2026-10-12 04:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0002_alter_embedding_dim_768'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Safely alter column type from vector(1536) to vector(768).
        # Existing NULL values and transcript records are preserved.
        op.alter_column(
            'transcript_chunks',
            'embedding',
            existing_type=Vector(1536),
            type_=Vector(768),
            existing_nullable=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.alter_column(
            'transcript_chunks',
            'embedding',
            existing_type=Vector(768),
            type_=Vector(1536),
            existing_nullable=True,
        )
