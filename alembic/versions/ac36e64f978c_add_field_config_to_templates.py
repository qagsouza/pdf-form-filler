"""add_field_config_to_templates

Revision ID: ac36e64f978c
Revises: a8c3f5d7b2e9
Create Date: 2025-12-05 07:26:19.870965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac36e64f978c'
down_revision: Union[str, Sequence[str], None] = 'a8c3f5d7b2e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add field_config column to templates table
    op.add_column('templates', sa.Column('field_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove field_config column from templates table
    op.drop_column('templates', 'field_config')
