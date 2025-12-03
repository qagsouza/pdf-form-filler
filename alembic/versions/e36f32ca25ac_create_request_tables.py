"""create_request_tables

Revision ID: e36f32ca25ac
Revises: 556f18da7e48
Create Date: 2025-12-03 08:31:55.359274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e36f32ca25ac'
down_revision: Union[str, Sequence[str], None] = '556f18da7e48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create requests table
    op.create_table(
        'requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('requester_id', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('SINGLE', 'BATCH', name='requesttype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='requeststatus'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requests_template_id'), 'requests', ['template_id'], unique=False)
    op.create_index(op.f('ix_requests_requester_id'), 'requests', ['requester_id'], unique=False)

    # Create request_instances table
    op.create_table(
        'request_instances',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('request_id', sa.String(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=True),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'SENT', name='instancestatus'), nullable=False),
        sa.Column('filled_pdf_path', sa.String(length=512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_instances_request_id'), 'request_instances', ['request_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_request_instances_request_id'), table_name='request_instances')
    op.drop_table('request_instances')
    op.drop_index(op.f('ix_requests_requester_id'), table_name='requests')
    op.drop_index(op.f('ix_requests_template_id'), table_name='requests')
    op.drop_table('requests')

    # Drop the enum types
    op.execute('DROP TYPE IF EXISTS requesttype')
    op.execute('DROP TYPE IF EXISTS requeststatus')
    op.execute('DROP TYPE IF EXISTS instancestatus')
