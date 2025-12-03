"""add email_sent to instances

Revision ID: f47b89d2e3c1
Revises: e36f32ca25ac
Create Date: 2025-12-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f47b89d2e3c1'
down_revision = 'e36f32ca25ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email_sent column to request_instances table
    op.add_column('request_instances', sa.Column('email_sent', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove email_sent column
    op.drop_column('request_instances', 'email_sent')
