"""create_resumes_tables

Revision ID: 14f47aa49fa6
Revises: 
Create Date: 2025-11-30 00:15:19.968860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '14f47aa49fa6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем таблицу resumes
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Создаем таблицу resume_sections
    op.create_table(
        'resume_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
    )

    # Создаем индекс для быстрого поиска по user_id
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'])
    
    # Создаем индекс для быстрого поиска секций по resume_id
    op.create_index('ix_resume_sections_resume_id', 'resume_sections', ['resume_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индексы
    op.drop_index('ix_resume_sections_resume_id', table_name='resume_sections')
    op.drop_index('ix_resumes_user_id', table_name='resumes')
    
    # Удаляем таблицы
    op.drop_table('resume_sections')
    op.drop_table('resumes')
