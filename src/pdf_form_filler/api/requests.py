"""
API routes for request management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_user
from ..models.user import User
from ..schemas.request import (
    RequestCreate,
    RequestWithData,
    RequestResponse,
    RequestDetailResponse,
    RequestListResponse,
    RequestStatsResponse,
    RequestInstanceResponse,
)
from ..services.request_service import RequestService
from ..services.storage_service import StorageService
from ..errors import PDFFormFillerError

router = APIRouter(prefix="/api/requests", tags=["requests"])

# Initialize services
storage_service = StorageService()
request_service = RequestService(storage_service)


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request_data: RequestWithData,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Create and process a new form filling request

    - **template_id**: ID of the template to use
    - **name**: Optional name for the request
    - **notes**: Optional notes
    - **data**: Form field data (key-value pairs)
    - **recipient_email**: Optional recipient email (for future email feature)
    - **recipient_name**: Optional recipient name
    """
    try:
        request = RequestService.create_request_with_instance(
            db=db,
            user_id=current_user.id,
            request_data=request_data,
            storage=storage_service
        )

        # Build response
        template_name = request.template.name if request.template else None

        return RequestResponse(
            **request.__dict__,
            instance_count=request.instance_count,
            completed_count=request.completed_count,
            failed_count=request.failed_count,
            template_name=template_name
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[RequestListResponse])
def list_requests(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List all requests created by current user

    - **limit**: Maximum number of results (default 100)
    - **offset**: Number of results to skip (default 0)
    """
    requests = RequestService.get_user_requests(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    response = []
    for request in requests:
        template_name = request.template.name if request.template else None
        response.append(
            RequestListResponse(
                **request.__dict__,
                template_name=template_name,
                instance_count=request.instance_count,
                completed_count=request.completed_count,
                failed_count=request.failed_count
            )
        )

    return response


@router.get("/stats", response_model=RequestStatsResponse)
def get_stats(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Get request statistics for current user
    """
    stats = RequestService.get_request_stats(db, current_user.id)
    return RequestStatsResponse(**stats)


@router.get("/{request_id}", response_model=RequestDetailResponse)
def get_request(
    request_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Get request details with all instances
    """
    request = RequestService.get_request(db, request_id, current_user.id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    # Build response with instances
    instances = [
        RequestInstanceResponse(**instance.__dict__)
        for instance in request.instances
    ]

    template_name = request.template.name if request.template else None

    return RequestDetailResponse(
        **request.__dict__,
        instances=instances,
        instance_count=request.instance_count,
        completed_count=request.completed_count,
        failed_count=request.failed_count,
        template_name=template_name
    )


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Delete a request and all its instances
    """
    try:
        deleted = RequestService.delete_request(
            db=db,
            request_id=request_id,
            user_id=current_user.id,
            storage=storage_service
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{request_id}/instances/{instance_id}/download")
async def download_filled_pdf(
    request_id: str,
    instance_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Download filled PDF for a specific instance
    """
    # Get instance
    instance = RequestService.get_instance(db, instance_id, current_user.id)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )

    if not instance.filled_pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filled PDF not available"
        )

    try:
        file_path = storage_service.get_filled_pdf_path(instance.filled_pdf_path)

        # Generate filename
        request = instance.request
        template_name = request.template.name if request.template else "form"
        safe_name = template_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_filled.pdf"

        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/pdf"
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
