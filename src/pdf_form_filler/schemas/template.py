"""
Pydantic schemas for templates
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import re


class TemplateBase(BaseModel):
    """Base template schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name"""
        if not v.strip():
            raise ValueError("Template name cannot be empty")
        # Remove extra whitespace
        return " ".join(v.split())


class TemplateCreate(TemplateBase):
    """Schema for creating a template"""
    pass


class TemplateUpdate(BaseModel):
    """Schema for updating a template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate template name"""
        if v is not None:
            if not v.strip():
                raise ValueError("Template name cannot be empty")
            return " ".join(v.split())
        return v


class TemplateFieldInfo(BaseModel):
    """Information about a PDF form field"""
    type: str  # text, button, choice, unknown
    page: int
    value: Optional[str] = None


class TemplateInDB(TemplateBase):
    """Template schema with all database fields"""
    id: str
    owner_id: str
    file_path: str
    original_filename: str
    fields_metadata: Optional[Dict[str, Dict[str, Any]]] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateResponse(TemplateInDB):
    """Template response with permission info"""
    permission: str = "none"  # owner, admin, editor, viewer, none
    is_owner: bool = False


class TemplateListResponse(BaseModel):
    """Response for listing templates"""
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    original_filename: str
    version: int
    created_at: datetime
    updated_at: datetime
    permission: str = "none"
    is_owner: bool = False
    field_count: int = 0

    model_config = {"from_attributes": True}


class TemplateFieldsResponse(BaseModel):
    """Response with template fields"""
    template_id: str
    template_name: str
    fields: Dict[str, TemplateFieldInfo]


# Template Sharing Schemas

class TemplateShareCreate(BaseModel):
    """Schema for sharing a template"""
    user_id: str = Field(..., description="ID of the user to share with")
    permission: str = Field("viewer", description="Permission level: viewer, editor, admin")

    @field_validator('permission')
    @classmethod
    def validate_permission(cls, v: str) -> str:
        """Validate permission level"""
        allowed = ["viewer", "editor", "admin"]
        if v.lower() not in allowed:
            raise ValueError(f"Permission must be one of: {', '.join(allowed)}")
        return v.lower()


class TemplateShareUpdate(BaseModel):
    """Schema for updating share permission"""
    permission: str = Field(..., description="Permission level: viewer, editor, admin")

    @field_validator('permission')
    @classmethod
    def validate_permission(cls, v: str) -> str:
        """Validate permission level"""
        allowed = ["viewer", "editor", "admin"]
        if v.lower() not in allowed:
            raise ValueError(f"Permission must be one of: {', '.join(allowed)}")
        return v.lower()


class TemplateShareResponse(BaseModel):
    """Response for template share"""
    id: str
    template_id: str
    user_id: str
    shared_by_id: Optional[str]
    permission: str
    created_at: datetime

    # Additional user info (populated from query)
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    shared_by_email: Optional[str] = None

    model_config = {"from_attributes": True}


class TemplateShareListResponse(BaseModel):
    """Response for listing template shares"""
    template_id: str
    template_name: str
    shares: List[TemplateShareResponse]
