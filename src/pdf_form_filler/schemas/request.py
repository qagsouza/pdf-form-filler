"""
Pydantic schemas for requests
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# Request Schemas

class RequestCreate(BaseModel):
    """Schema for creating a request"""
    template_id: str = Field(..., description="Template ID to use")
    name: Optional[str] = Field(None, max_length=255, description="Optional request name")
    notes: Optional[str] = Field(None, max_length=2000, description="Optional notes")


class RequestInstanceCreate(BaseModel):
    """Schema for creating a request instance"""
    data: Dict[str, Any] = Field(..., description="Form field data")
    recipient_email: Optional[str] = Field(None, description="Optional recipient email")
    recipient_name: Optional[str] = Field(None, max_length=255, description="Optional recipient name")


class RequestWithData(BaseModel):
    """Schema for creating a request with instance data"""
    template_id: str = Field(..., description="Template ID to use")
    name: Optional[str] = Field(None, max_length=255, description="Optional request name")
    notes: Optional[str] = Field(None, max_length=2000, description="Optional notes")
    data: Dict[str, Any] = Field(..., description="Form field data")
    recipient_email: Optional[str] = Field(None, description="Optional recipient email")
    recipient_name: Optional[str] = Field(None, max_length=255, description="Optional recipient name")


# Response Schemas

class RequestInstanceResponse(BaseModel):
    """Response for request instance"""
    id: str
    request_id: str
    data: Dict[str, Any]
    recipient_email: Optional[str]
    recipient_name: Optional[str]
    status: str
    filled_pdf_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RequestResponse(BaseModel):
    """Response for request"""
    id: str
    template_id: str
    requester_id: str
    type: str
    status: str
    name: Optional[str]
    notes: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    # Computed fields
    instance_count: int = 0
    completed_count: int = 0
    failed_count: int = 0

    # Optional template info
    template_name: Optional[str] = None

    model_config = {"from_attributes": True}


class RequestDetailResponse(RequestResponse):
    """Detailed response for request with instances"""
    instances: List[RequestInstanceResponse] = []


class RequestListResponse(BaseModel):
    """Response for listing requests"""
    id: str
    template_id: str
    template_name: Optional[str]
    type: str
    status: str
    name: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    instance_count: int
    completed_count: int
    failed_count: int

    model_config = {"from_attributes": True}


# Statistics

class RequestStatsResponse(BaseModel):
    """Response for request statistics"""
    total_requests: int = 0
    pending_requests: int = 0
    processing_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    total_instances: int = 0
    completed_instances: int = 0
    failed_instances: int = 0
