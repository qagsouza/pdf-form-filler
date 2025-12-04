"""add default_values to templates

Revision ID: a8c3f5d7b2e9
Revises: a8f9b3c4d5e6
Create Date: 2025-12-04 09:24:15.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8c3f5d7b2e9'
down_revision = 'a8f9b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add default_values column to templates table
    op.add_column('templates', sa.Column('default_values', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove default_values column
    op.drop_column('templates', 'default_values')
