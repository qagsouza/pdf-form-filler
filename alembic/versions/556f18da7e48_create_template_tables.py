"""create_template_tables

Revision ID: 556f18da7e48
Revises: b6bf573d4cb1
Create Date: 2025-12-03 08:16:24.870507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '556f18da7e48'
down_revision: Union[str, Sequence[str], None] = 'b6bf573d4cb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('fields_metadata', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_templates_owner_id'), 'templates', ['owner_id'], unique=False)

    # Create template_shares table
    op.create_table(
        'template_shares',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('shared_by_id', sa.String(), nullable=True),
        sa.Column('permission', sa.Enum('VIEWER', 'EDITOR', 'ADMIN', name='permissionlevel'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_shares_template_id'), 'template_shares', ['template_id'], unique=False)
    op.create_index(op.f('ix_template_shares_user_id'), 'template_shares', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_template_shares_user_id'), table_name='template_shares')
    op.drop_index(op.f('ix_template_shares_template_id'), table_name='template_shares')
    op.drop_table('template_shares')
    op.drop_index(op.f('ix_templates_owner_id'), table_name='templates')
    op.drop_table('templates')

    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS permissionlevel')
