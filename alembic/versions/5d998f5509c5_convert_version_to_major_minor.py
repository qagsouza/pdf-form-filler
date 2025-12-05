"""convert_version_to_major_minor

Revision ID: 5d998f5509c5
Revises: 303d2cf5bd9c
Create Date: 2025-12-05 09:05:43.386366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d998f5509c5'
down_revision: Union[str, Sequence[str], None] = '303d2cf5bd9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new version_major and version_minor columns with default values
    op.add_column('templates', sa.Column('version_major', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('templates', sa.Column('version_minor', sa.Integer(), nullable=False, server_default='0'))

    # Migrate existing version data to version_major
    # For SQLite, we need to use execute with proper SQL
    connection = op.get_bind()
    connection.execute(sa.text('UPDATE templates SET version_major = version, version_minor = 0'))

    # Drop the old version column
    op.drop_column('templates', 'version')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add the old version column
    op.add_column('templates', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    # Migrate version_major back to version
    connection = op.get_bind()
    connection.execute(sa.text('UPDATE templates SET version = version_major'))

    # Drop the new columns
    op.drop_column('templates', 'version_minor')
    op.drop_column('templates', 'version_major')
