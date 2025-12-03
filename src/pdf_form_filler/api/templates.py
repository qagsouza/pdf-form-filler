"""
API routes for template management
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_user, require_admin
from ..models.user import User
from ..schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateFieldsResponse,
    TemplateShareCreate,
    TemplateShareUpdate,
    TemplateShareResponse,
    TemplateShareListResponse,
    TemplateFieldInfo,
)
from ..services.template_service import TemplateService
from ..services.storage_service import StorageService
from ..errors import PDFFormFillerError

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Initialize services
storage_service = StorageService()
template_service = TemplateService(storage_service)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    name: str,
    description: str = None,
    file: UploadFile = File(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Create a new template by uploading a PDF

    - **name**: Template name
    - **description**: Optional description
    - **file**: PDF file to upload
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    # Validate file size (10MB max)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 10MB"
        )

    try:
        template_data = TemplateCreate(name=name, description=description)
        template = TemplateService.create_template(
            db=db,
            user_id=current_user.id,
            template_data=template_data,
            file=file,
            storage=storage_service
        )

        return TemplateResponse(
            **template.__dict__,
            permission="owner",
            is_owner=True
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[TemplateListResponse])
def list_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List all templates accessible by current user (owned + shared)
    """
    templates = TemplateService.get_all_accessible_templates(db, current_user.id)

    response = []
    for template in templates:
        permission = template.get_permission_for_user(current_user.id)
        is_owner = template.owner_id == current_user.id
        field_count = len(template.fields_metadata) if template.fields_metadata else 0

        response.append(
            TemplateListResponse(
                **template.__dict__,
                permission=permission,
                is_owner=is_owner,
                field_count=field_count
            )
        )

    return response


@router.get("/my-templates", response_model=List[TemplateListResponse])
def list_my_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List templates owned by current user
    """
    templates = TemplateService.get_user_templates(db, current_user.id)

    response = []
    for template in templates:
        field_count = len(template.fields_metadata) if template.fields_metadata else 0
        response.append(
            TemplateListResponse(
                **template.__dict__,
                permission="owner",
                is_owner=True,
                field_count=field_count
            )
        )

    return response


@router.get("/shared", response_model=List[TemplateListResponse])
def list_shared_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List templates shared with current user
    """
    templates = TemplateService.get_shared_templates(db, current_user.id)

    response = []
    for template in templates:
        permission = template.get_permission_for_user(current_user.id)
        field_count = len(template.fields_metadata) if template.fields_metadata else 0

        response.append(
            TemplateListResponse(
                **template.__dict__,
                permission=permission,
                is_owner=False,
                field_count=field_count
            )
        )

    return response


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Get template details by ID
    """
    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    permission = template.get_permission_for_user(current_user.id)
    is_owner = template.owner_id == current_user.id

    return TemplateResponse(
        **template.__dict__,
        permission=permission,
        is_owner=is_owner
    )


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Update template metadata

    Requires editor permission or higher
    """
    try:
        template = TemplateService.update_template(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
            template_data=template_data
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or insufficient permissions"
            )

        permission = template.get_permission_for_user(current_user.id)
        is_owner = template.owner_id == current_user.id

        return TemplateResponse(
            **template.__dict__,
            permission=permission,
            is_owner=is_owner
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Delete template

    Only the owner can delete a template
    """
    try:
        deleted = TemplateService.delete_template(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
            storage=storage_service
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or insufficient permissions"
            )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{template_id}/fields", response_model=TemplateFieldsResponse)
def get_template_fields(
    template_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Get template fields for filling
    """
    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    try:
        fields = TemplateService.get_template_fields(template, storage_service)

        # Convert to response format
        fields_response = {}
        for field_name, field_data in fields.items():
            fields_response[field_name] = TemplateFieldInfo(**field_data)

        return TemplateFieldsResponse(
            template_id=template.id,
            template_name=template.name,
            fields=fields_response
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Sharing endpoints

@router.post("/{template_id}/share", response_model=TemplateShareResponse, status_code=status.HTTP_201_CREATED)
def share_template(
    template_id: str,
    share_data: TemplateShareCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Share template with another user

    Requires admin permission or owner
    """
    try:
        share = TemplateService.share_template(
            db=db,
            template_id=template_id,
            current_user_id=current_user.id,
            share_data=share_data
        )

        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or insufficient permissions"
            )

        # Get user info
        user = db.query(User).filter(User.id == share.user_id).first()
        shared_by = db.query(User).filter(User.id == share.shared_by_id).first()

        return TemplateShareResponse(
            **share.__dict__,
            permission=share.permission.value,
            user_email=user.email if user else None,
            user_full_name=user.full_name if user else None,
            shared_by_email=shared_by.email if shared_by else None
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{template_id}/shares", response_model=TemplateShareListResponse)
def list_template_shares(
    template_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List all shares for a template

    Only owner or admin can view shares
    """
    shares = TemplateService.get_template_shares(db, template_id, current_user.id)

    if shares is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or insufficient permissions"
        )

    template = TemplateService.get_template(db, template_id, current_user.id)

    # Enrich with user info
    response_shares = []
    for share in shares:
        user = db.query(User).filter(User.id == share.user_id).first()
        shared_by = db.query(User).filter(User.id == share.shared_by_id).first()

        response_shares.append(
            TemplateShareResponse(
                **share.__dict__,
                permission=share.permission.value,
                user_email=user.email if user else None,
                user_full_name=user.full_name if user else None,
                shared_by_email=shared_by.email if shared_by else None
            )
        )

    return TemplateShareListResponse(
        template_id=template.id,
        template_name=template.name,
        shares=response_shares
    )


@router.put("/{template_id}/share/{share_id}", response_model=TemplateShareResponse)
def update_share(
    template_id: str,
    share_id: str,
    update_data: TemplateShareUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Update share permission

    Requires admin permission or owner
    """
    try:
        share = TemplateService.update_share(
            db=db,
            share_id=share_id,
            current_user_id=current_user.id,
            update_data=update_data
        )

        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or insufficient permissions"
            )

        # Get user info
        user = db.query(User).filter(User.id == share.user_id).first()
        shared_by = db.query(User).filter(User.id == share.shared_by_id).first()

        return TemplateShareResponse(
            **share.__dict__,
            permission=share.permission.value,
            user_email=user.email if user else None,
            user_full_name=user.full_name if user else None,
            shared_by_email=shared_by.email if shared_by else None
        )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{template_id}/share/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_share(
    template_id: str,
    share_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Remove template share

    Requires admin permission or owner
    """
    try:
        removed = TemplateService.remove_share(
            db=db,
            share_id=share_id,
            current_user_id=current_user.id
        )

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or insufficient permissions"
            )

    except PDFFormFillerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
