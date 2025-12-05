"""
Group models for organizing users
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Group(Base):
    """
    Group model for organizing users

    Allows grouping users together for easier template sharing
    """
    __tablename__ = "groups"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Owner of the group
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", backref="owned_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name}, owner_id={self.owner_id})>"

    @property
    def member_count(self) -> int:
        """Get number of members (excluding owner)"""
        return len(self.members)

    def has_member(self, user_id: str) -> bool:
        """Check if user is a member of this group"""
        if user_id == self.owner_id:
            return True
        return any(m.user_id == user_id for m in self.members)


class GroupMember(Base):
    """
    Group membership model

    Represents membership of a user in a group
    """
    __tablename__ = "group_members"

    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", backref="group_memberships")

    def __repr__(self):
        return f"<GroupMember(group_id={self.group_id}, user_id={self.user_id})>"
