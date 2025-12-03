"""
Request models for PDF form filling
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .template import Template


class RequestType(enum.Enum):
    """Types of requests"""
    SINGLE = "single"  # Single form filling
    BATCH = "batch"    # Multiple forms (future)


class RequestStatus(enum.Enum):
    """Request status"""
    PENDING = "pending"        # Waiting to be processed
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed with errors


class Request(Base):
    """
    Request model for PDF form filling

    Represents a request to fill one or more PDF forms
    """
    __tablename__ = "requests"

    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    requester_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    type = Column(SQLEnum(RequestType), nullable=False, default=RequestType.SINGLE)
    status = Column(SQLEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING)

    # Metadata
    name = Column(String(255), nullable=True)  # Optional name for the request
    notes = Column(Text, nullable=True)        # Optional notes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    template = relationship("Template", backref="requests")
    requester = relationship("User", backref="requests")
    instances = relationship("RequestInstance", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Request(id={self.id}, type={self.type.value}, status={self.status.value})>"

    @property
    def instance_count(self) -> int:
        """Get number of instances"""
        return len(self.instances)

    @property
    def completed_count(self) -> int:
        """Get number of completed instances"""
        return sum(1 for i in self.instances if i.status == InstanceStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        """Get number of failed instances"""
        return sum(1 for i in self.instances if i.status == InstanceStatus.FAILED)


class InstanceStatus(enum.Enum):
    """Instance status"""
    PENDING = "pending"        # Waiting to be processed
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed with errors
    SENT = "sent"             # Email sent (future)


class RequestInstance(Base):
    """
    Request instance model

    Represents a single PDF form filling within a request
    For single requests, there's only one instance
    For batch requests, there are multiple instances
    """
    __tablename__ = "request_instances"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)

    # Form data (JSON with field values)
    data = Column(JSON, nullable=False)

    # Optional recipient info (for future email feature)
    recipient_email = Column(String, nullable=True)
    recipient_name = Column(String, nullable=True)

    # Status
    status = Column(SQLEnum(InstanceStatus), nullable=False, default=InstanceStatus.PENDING)

    # Result
    filled_pdf_path = Column(String(512), nullable=True)  # Path to filled PDF
    error_message = Column(Text, nullable=True)            # Error message if failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    request = relationship("Request", back_populates="instances")

    def __repr__(self):
        return f"<RequestInstance(id={self.id}, request_id={self.request_id}, status={self.status.value})>"

    @property
    def is_completed(self) -> bool:
        """Check if instance is completed"""
        return self.status == InstanceStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if instance failed"""
        return self.status == InstanceStatus.FAILED

    @property
    def is_pending(self) -> bool:
        """Check if instance is pending"""
        return self.status == InstanceStatus.PENDING
