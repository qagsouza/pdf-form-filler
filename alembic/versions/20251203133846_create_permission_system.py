"""create permission system

Revision ID: a8f9b3c4d5e6
Revises: f47b89d2e3c1
Create Date: 2025-12-03 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = 'a8f9b3c4d5e6'
down_revision = 'f47b89d2e3c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'])
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_index('ix_permissions_action', 'permissions', ['action'])

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.String(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_roles_name', 'roles', ['name'])

    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('permission_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Insert default permissions
    now = datetime.utcnow()
    permissions = [
        # Template permissions
        {'id': str(uuid.uuid4()), 'name': 'template.create', 'description': 'Create templates', 'resource': 'template', 'action': 'create', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'template.read', 'description': 'View templates', 'resource': 'template', 'action': 'read', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'template.update', 'description': 'Edit templates', 'resource': 'template', 'action': 'update', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'template.delete', 'description': 'Delete templates', 'resource': 'template', 'action': 'delete', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'template.share', 'description': 'Share templates', 'resource': 'template', 'action': 'share', 'created_at': now},
        
        # Request permissions
        {'id': str(uuid.uuid4()), 'name': 'request.create', 'description': 'Create form fill requests', 'resource': 'request', 'action': 'create', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'request.read', 'description': 'View requests', 'resource': 'request', 'action': 'read', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'request.delete', 'description': 'Delete requests', 'resource': 'request', 'action': 'delete', 'created_at': now},
        
        # Batch permissions
        {'id': str(uuid.uuid4()), 'name': 'batch.create', 'description': 'Create batch requests', 'resource': 'batch', 'action': 'create', 'created_at': now},
        
        # User management permissions
        {'id': str(uuid.uuid4()), 'name': 'user.read', 'description': 'View users', 'resource': 'user', 'action': 'read', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'user.update', 'description': 'Edit users', 'resource': 'user', 'action': 'update', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'user.delete', 'description': 'Delete users', 'resource': 'user', 'action': 'delete', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'user.manage_roles', 'description': 'Manage user roles', 'resource': 'user', 'action': 'manage_roles', 'created_at': now},
        
        # Role management permissions
        {'id': str(uuid.uuid4()), 'name': 'role.create', 'description': 'Create roles', 'resource': 'role', 'action': 'create', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'role.read', 'description': 'View roles', 'resource': 'role', 'action': 'read', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'role.update', 'description': 'Edit roles', 'resource': 'role', 'action': 'update', 'created_at': now},
        {'id': str(uuid.uuid4()), 'name': 'role.delete', 'description': 'Delete roles', 'resource': 'role', 'action': 'delete', 'created_at': now},
    ]

    op.bulk_insert(
        sa.table('permissions',
            sa.column('id', sa.String),
            sa.column('name', sa.String),
            sa.column('description', sa.Text),
            sa.column('resource', sa.String),
            sa.column('action', sa.String),
            sa.column('created_at', sa.DateTime),
        ),
        permissions
    )

    # Insert default roles
    role_admin_id = str(uuid.uuid4())
    role_editor_id = str(uuid.uuid4())
    role_viewer_id = str(uuid.uuid4())

    roles = [
        {'id': role_admin_id, 'name': 'admin', 'description': 'Full system access', 'is_system': 'true', 'created_at': now},
        {'id': role_editor_id, 'name': 'editor', 'description': 'Can create and edit templates and requests', 'is_system': 'true', 'created_at': now},
        {'id': role_viewer_id, 'name': 'viewer', 'description': 'Can only view templates and create requests', 'is_system': 'true', 'created_at': now},
    ]

    op.bulk_insert(
        sa.table('roles',
            sa.column('id', sa.String),
            sa.column('name', sa.String),
            sa.column('description', sa.Text),
            sa.column('is_system', sa.String),
            sa.column('created_at', sa.DateTime),
        ),
        roles
    )

    # Assign permissions to roles
    # Get permission IDs (we'll need to query them)
    conn = op.get_bind()
    perm_result = conn.execute(sa.text("SELECT id, name FROM permissions"))
    perm_map = {row[1]: row[0] for row in perm_result}

    # Admin role - all permissions
    admin_perms = []
    for perm_name, perm_id in perm_map.items():
        admin_perms.append({'role_id': role_admin_id, 'permission_id': perm_id, 'created_at': now})

    # Editor role - can create/edit templates and requests
    editor_perm_names = [
        'template.create', 'template.read', 'template.update', 'template.share',
        'request.create', 'request.read', 'request.delete',
        'batch.create'
    ]
    editor_perms = [
        {'role_id': role_editor_id, 'permission_id': perm_map[name], 'created_at': now}
        for name in editor_perm_names if name in perm_map
    ]

    # Viewer role - can only view and create requests
    viewer_perm_names = ['template.read', 'request.create', 'request.read', 'batch.create']
    viewer_perms = [
        {'role_id': role_viewer_id, 'permission_id': perm_map[name], 'created_at': now}
        for name in viewer_perm_names if name in perm_map
    ]

    op.bulk_insert(
        sa.table('role_permissions',
            sa.column('role_id', sa.String),
            sa.column('permission_id', sa.String),
            sa.column('created_at', sa.DateTime),
        ),
        admin_perms + editor_perms + viewer_perms
    )


def downgrade() -> None:
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_index('ix_roles_name', 'roles')
    op.drop_table('roles')
    op.drop_index('ix_permissions_action', 'permissions')
    op.drop_index('ix_permissions_resource', 'permissions')
    op.drop_index('ix_permissions_name', 'permissions')
    op.drop_table('permissions')
