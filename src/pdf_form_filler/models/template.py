"""
Template models for PDF forms
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Template(Base):
    """
    PDF Template model

    Represents a PDF form template that can be filled multiple times
    """
    __tablename__ = "templates"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)

    # Metadata about the PDF fields
    fields_metadata = Column(JSON, nullable=True)

    # Default values for fields
    default_values = Column(JSON, nullable=True)

    # Field configuration: locked status, dynamic values
    # Format: {field_name: {"locked": bool, "dynamic_type": str|null}}
    field_config = Column(JSON, nullable=True)

    # Sequence number counter for serial_number dynamic type
    sequence_number = Column(Integer, default=0, nullable=False)

    # Versioning (semantic versioning: major.minor)
    version_major = Column(Integer, default=1, nullable=False)
    version_minor = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="templates")
    shares = relationship("TemplateShare", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, owner_id={self.owner_id})>"

    @property
    def version(self) -> str:
        """Get formatted version string (major.minor)"""
        return f"{self.version_major}.{self.version_minor}"

    def is_accessible_by(self, user_id: str) -> bool:
        """Check if user has access to this template"""
        if self.owner_id == user_id:
            return True

        # Check if shared with user
        for share in self.shares:
            if share.user_id == user_id:
                return True

        return False

    def get_permission_for_user(self, user_id: str) -> str:
        """Get user's permission level for this template (considering both direct shares and group shares)"""
        if self.owner_id == user_id:
            return "owner"

        # Check direct user shares
        for share in self.shares:
            if share.user_id == user_id:
                return share.permission.value

        # Check group shares
        from .group import GroupMember
        for share in self.shares:
            if share.group_id:
                # Check if user is a member of this group
                for member in share.group.members:
                    if member.user_id == user_id:
                        return share.permission.value
                # Also check if user is the group owner
                if share.group.owner_id == user_id:
                    return share.permission.value

        return "none"


class PermissionLevel(enum.Enum):
    """Permission levels for template sharing"""
    VIEWER = "viewer"  # Can view and use template
    EDITOR = "editor"  # Can view, use and edit template
    ADMIN = "admin"    # Can view, use, edit and manage sharing


class TemplateShare(Base):
    """
    Template sharing model

    Represents sharing a template with another user or group
    Can share with either a user OR a group (not both)
    """
    __tablename__ = "template_shares"

    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)

    # Share with either user OR group (one must be NULL)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    group_id = Column(String, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)

    shared_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    permission = Column(SQLEnum(PermissionLevel), nullable=False, default=PermissionLevel.VIEWER)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("Template", back_populates="shares")
    user = relationship("User", foreign_keys=[user_id], back_populates="shared_templates")
    group = relationship("Group", foreign_keys=[group_id])
    shared_by = relationship("User", foreign_keys=[shared_by_id])

    def __repr__(self):
        target = f"user_id={self.user_id}" if self.user_id else f"group_id={self.group_id}"
        return f"<TemplateShare(template_id={self.template_id}, {target}, permission={self.permission})>"
