"""
User model
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from ..database import Base

if TYPE_CHECKING:
    from .permission import Role


class User(Base):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID as string
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # "admin" or "user"
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)  # Requires admin approval
    email_verification_token = Column(String, nullable=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    templates = relationship("Template", back_populates="owner", cascade="all, delete-orphan")
    shared_templates = relationship(
        "TemplateShare",
        foreign_keys="TemplateShare.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Will be set up after permission module is loaded
    # roles = relationship("Role", secondary="user_roles", back_populates="users")

    def is_admin(self, db=None) -> bool:
        """
        Check if user has admin role via RBAC

        Args:
            db: Database session (optional)

        Returns:
            True if user has the 'admin' role
        """
        # Get roles from database
        from sqlalchemy.orm import Session
        from .permission import Role, user_roles

        # Get session
        if db is None:
            from sqlalchemy import inspect
            db = inspect(self).session
            if db is None:
                # Fallback to legacy role field for backwards compatibility
                return self.role == "admin"

        # Check if user has 'admin' role via RBAC
        admin_role = db.query(Role).join(user_roles).filter(
            user_roles.c.user_id == self.id,
            Role.name == "admin"
        ).first()

        # If has admin role via RBAC, return True
        if admin_role:
            return True

        # Fallback to legacy role field for backwards compatibility during migration
        return self.role == "admin"

    def has_permission(self, permission_name: str, db=None) -> bool:
        """
        Check if user has a specific permission

        Args:
            permission_name: Permission name (e.g., "template.create")
                           Can use wildcards (e.g., "template.*", "admin.*")
            db: Database session (optional, will use object session if available)

        Returns:
            True if user has the permission
        """
        # Admin role has all permissions (check via RBAC first, then legacy)
        if self.is_admin(db):
            return True

        # Get roles from database
        from sqlalchemy.orm import Session
        from .permission import Role, user_roles

        # Get session
        if db is None:
            from sqlalchemy import inspect
            db = inspect(self).session
            if db is None:
                # No session available, assume no permissions
                return False

        # Get user roles
        roles = db.query(Role).join(user_roles).filter(user_roles.c.user_id == self.id).all()

        # Check if user has the permission through any of their roles
        for role in roles:
            for perm in role.permissions:
                # Exact match
                if perm.name == permission_name:
                    return True

                # Wildcard match (e.g., "template.*" matches "template.create")
                if permission_name.endswith(".*"):
                    resource = permission_name.split(".")[0]
                    if perm.resource == resource:
                        return True

                # Permission has wildcard
                if perm.name.endswith(".*"):
                    resource = perm.name.split(".")[0]
                    if permission_name.startswith(resource + "."):
                        return True

        return False

    def get_all_permissions(self, db=None) -> list[str]:
        """Get list of all permission names for this user"""
        if self.role == "admin":
            return ["admin.*"]

        # Get roles from database
        from sqlalchemy.orm import Session
        from .permission import Role, user_roles

        # Get session
        if db is None:
            from sqlalchemy import inspect
            db = inspect(self).session
            if db is None:
                return []

        # Get user roles
        roles = db.query(Role).join(user_roles).filter(user_roles.c.user_id == self.id).all()

        permissions = set()
        for role in roles:
            permissions.update(role.get_permission_names())

        return sorted(list(permissions))

    def __repr__(self):
        return f"<User {self.email}>"
