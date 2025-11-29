"""add_cover_letter_to_resume_versions

Revision ID: 9fcd59c326c6
Revises: 1540831cc7b9
Create Date: 2025-11-30 01:49:05.083030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fcd59c326c6'
down_revision: Union[str, None] = '1540831cc7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'resume_versions',
        sa.Column('cover_letter', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('resume_versions', 'cover_letter')
