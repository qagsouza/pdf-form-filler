"""add_request_number_field

Revision ID: 42d1ed04a733
Revises: 5d998f5509c5
Create Date: 2025-12-05 15:31:27.767800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42d1ed04a733'
down_revision: Union[str, Sequence[str], None] = '5d998f5509c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, use batch mode
    with op.batch_alter_table('requests') as batch_op:
        batch_op.add_column(sa.Column('request_number', sa.String(20), nullable=True))
        batch_op.create_unique_constraint('uq_requests_request_number', ['request_number'])


def downgrade() -> None:
    """Downgrade schema."""
    # For SQLite, use batch mode
    with op.batch_alter_table('requests') as batch_op:
        batch_op.drop_constraint('uq_requests_request_number', type_='unique')
        batch_op.drop_column('request_number')
