"""add_sequence_number_to_templates

Revision ID: 303d2cf5bd9c
Revises: ac36e64f978c
Create Date: 2025-12-05 08:34:34.839653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '303d2cf5bd9c'
down_revision: Union[str, Sequence[str], None] = 'ac36e64f978c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add sequence_number column to templates table
    op.add_column('templates', sa.Column('sequence_number', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove sequence_number column from templates table
    op.drop_column('templates', 'sequence_number')
