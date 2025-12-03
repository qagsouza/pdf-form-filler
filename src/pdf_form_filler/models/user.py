"""
User model
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from ..database import Base


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

    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"
