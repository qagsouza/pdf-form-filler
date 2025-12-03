"""
User schemas for validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base user schema"""

    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only alphanumeric and underscore"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration"""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user"""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""

    id: str
    role: str
    is_active: bool
    is_verified: bool
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True
