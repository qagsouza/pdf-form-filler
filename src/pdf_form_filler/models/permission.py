"""
Permission and Role models for RBAC system
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', String, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', String, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Permission(Base):
    """
    Permission model - represents a single permission
    
    Examples: template.create, template.delete, request.read
    """
    __tablename__ = "permissions"

    id = Column(String, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False, index=True)  # e.g., "template", "request"
    action = Column(String(50), nullable=False, index=True)    # e.g., "create", "read", "update", "delete"
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(name={self.name})>"

    @property
    def full_name(self) -> str:
        """Get full permission name (resource.action)"""
        return f"{self.resource}.{self.action}"


class Role(Base):
    """
    Role model - groups multiple permissions
    
    Examples: admin, editor, viewer, template_manager
    """
    __tablename__ = "roles"

    id = Column(String, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(String, default="false", nullable=False)  # System roles can't be deleted
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        return f"<Role(name={self.name})>"

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission"""
        return any(p.name == permission_name for p in self.permissions)

    def get_permission_names(self) -> list[str]:
        """Get list of all permission names"""
        return [p.name for p in self.permissions]
