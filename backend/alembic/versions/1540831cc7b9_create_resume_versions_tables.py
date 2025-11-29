"""create_resume_versions_tables

Revision ID: 1540831cc7b9
Revises: 14f47aa49fa6
Create Date: 2025-11-30 01:46:59.979250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1540831cc7b9'
down_revision: Union[str, None] = '14f47aa49fa6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем таблицу resume_versions
    op.create_table(
        'resume_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
    )

    # Создаем таблицу resume_version_sections
    op.create_table(
        'resume_version_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['resume_versions.id'], ondelete='CASCADE'),
    )

    # Создаем индексы
    op.create_index('ix_resume_versions_resume_id', 'resume_versions', ['resume_id'])
    op.create_index('ix_resume_version_sections_version_id', 'resume_version_sections', ['version_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индексы
    op.drop_index('ix_resume_version_sections_version_id', table_name='resume_version_sections')
    op.drop_index('ix_resume_versions_resume_id', table_name='resume_versions')
    
    # Удаляем таблицы
    op.drop_table('resume_version_sections')
    op.drop_table('resume_versions')
