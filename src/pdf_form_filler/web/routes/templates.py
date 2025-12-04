"""
Web routes for template management
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...database import get_db
from ...dependencies import get_current_user, require_user
from ...models.user import User
from ...schemas.template import TemplateCreate, TemplateUpdate, TemplateShareCreate
from ...services.template_service import TemplateService
from ...services.storage_service import StorageService
from ...services.excel_service import ExcelService
from ...errors import PDFFormFillerError

router = APIRouter(tags=["web-templates"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")

# Initialize services
storage_service = StorageService()
template_service = TemplateService(storage_service)


@router.get("/templates", response_class=HTMLResponse)
def templates_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show templates management page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Get user's templates
    owned_templates = TemplateService.get_user_templates(db, current_user.id)
    shared_templates = TemplateService.get_shared_templates(db, current_user.id)

    # Add permission info
    owned_list = []
    for template in owned_templates:
        field_count = len(template.fields_metadata) if template.fields_metadata else 0
        owned_list.append({
            "template": template,
            "permission": "owner",
            "is_owner": True,
            "field_count": field_count
        })

    shared_list = []
    for template in shared_templates:
        permission = template.get_permission_for_user(current_user.id)
        field_count = len(template.fields_metadata) if template.fields_metadata else 0
        shared_list.append({
            "template": template,
            "permission": permission,
            "is_owner": False,
            "field_count": field_count
        })

    return templates.TemplateResponse(
        request,
        "templates/list.html",
        {
            "owned_templates": owned_list,
            "shared_templates": shared_list,
            "current_user": current_user
        }
    )


@router.post("/templates/create")
async def create_template(
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new template"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        return RedirectResponse(
            url="/templates?error=invalid_file",
            status_code=302
        )

    try:
        template_data = TemplateCreate(name=name, description=description)
        TemplateService.create_template(
            db=db,
            user_id=current_user.id,
            template_data=template_data,
            file=file,
            storage=storage_service
        )

        return RedirectResponse(
            url="/templates?success=template_created",
            status_code=302
        )

    except PDFFormFillerError as e:
        return RedirectResponse(
            url=f"/templates?error=create_failed",
            status_code=302
        )


@router.get("/templates/{template_id}", response_class=HTMLResponse)
def template_details(
    template_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show template details page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        return RedirectResponse(url="/templates?error=not_found", status_code=302)

    permission = template.get_permission_for_user(current_user.id)
    is_owner = template.owner_id == current_user.id

    # Get fields
    try:
        fields = TemplateService.get_template_fields(template, storage_service)
    except PDFFormFillerError:
        fields = {}

    # Get shares (only if owner or admin)
    shares = None
    if permission in ["owner", "admin"]:
        shares = TemplateService.get_template_shares(db, template_id, current_user.id)
        # Enrich with user info
        shares_with_users = []
        if shares:
            for share in shares:
                user = db.query(User).filter(User.id == share.user_id).first()
                shares_with_users.append({
                    "share": share,
                    "user": user
                })
        shares = shares_with_users

    return templates.TemplateResponse(
        request,
        "templates/details.html",
        {
            "template": template,
            "permission": permission,
            "is_owner": is_owner,
            "fields": fields,
            "field_count": len(fields),
            "shares": shares,
            "current_user": current_user
        }
    )


@router.post("/templates/{template_id}/update")
async def update_template(
    template_id: str,
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update template metadata"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        template_data = TemplateUpdate(name=name, description=description)
        template = TemplateService.update_template(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
            template_data=template_data
        )

        if not template:
            return RedirectResponse(
                url="/templates?error=not_found",
                status_code=302
            )

        return RedirectResponse(
            url=f"/templates/{template_id}?success=updated",
            status_code=302
        )

    except PDFFormFillerError:
        return RedirectResponse(
            url=f"/templates/{template_id}?error=update_failed",
            status_code=302
        )


@router.post("/templates/{template_id}/delete")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete template"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        deleted = TemplateService.delete_template(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
            storage=storage_service
        )

        if not deleted:
            return RedirectResponse(
                url="/templates?error=delete_failed",
                status_code=302
            )

        return RedirectResponse(
            url="/templates?success=deleted",
            status_code=302
        )

    except PDFFormFillerError:
        return RedirectResponse(
            url="/templates?error=delete_failed",
            status_code=302
        )


@router.get("/templates/{template_id}/download")
async def download_template(
    template_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Download template PDF"""
    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        file_path = storage_service.get_template_path(template.file_path)

        # Return FileResponse with headers that allow inline viewing
        from fastapi.responses import FileResponse
        response = FileResponse(
            file_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{template.original_filename}"'
            }
        )
        return response

    except PDFFormFillerError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/templates/{template_id}/share")
async def share_template(
    template_id: str,
    user_email: str = Form(...),
    permission: str = Form("viewer"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share template with user"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Find user by email
    target_user = db.query(User).filter(User.email == user_email).first()

    if not target_user:
        return RedirectResponse(
            url=f"/templates/{template_id}?error=user_not_found",
            status_code=302
        )

    try:
        share_data = TemplateShareCreate(
            user_id=target_user.id,
            permission=permission
        )

        TemplateService.share_template(
            db=db,
            template_id=template_id,
            current_user_id=current_user.id,
            share_data=share_data
        )

        return RedirectResponse(
            url=f"/templates/{template_id}?success=shared",
            status_code=302
        )

    except PDFFormFillerError as e:
        return RedirectResponse(
            url=f"/templates/{template_id}?error=share_failed",
            status_code=302
        )


@router.post("/templates/{template_id}/share/{share_id}/remove")
async def remove_share(
    template_id: str,
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove template share"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        removed = TemplateService.remove_share(
            db=db,
            share_id=share_id,
            current_user_id=current_user.id
        )

        if not removed:
            return RedirectResponse(
                url=f"/templates/{template_id}?error=remove_failed",
                status_code=302
            )

        return RedirectResponse(
            url=f"/templates/{template_id}?success=share_removed",
            status_code=302
        )

    except PDFFormFillerError:
        return RedirectResponse(
            url=f"/templates/{template_id}?error=remove_failed",
            status_code=302
        )


@router.get("/templates/{template_id}/download-excel")
def download_excel_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download Excel template with form field names"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        storage = StorageService()

        # Get template fields
        fields = TemplateService.get_template_fields(template, storage)

        # Get field names
        field_names = list(fields.keys())

        # Add special columns for email
        field_names.append("_recipient_email")
        field_names.append("_recipient_name")

        # Create Excel template
        temp_path = storage.create_temp_file(".xlsx")
        ExcelService.create_template(field_names, str(temp_path))

        # Generate filename
        safe_name = template.name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_batch_template.xlsx"

        return FileResponse(
            temp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except PDFFormFillerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/default-values")
async def save_default_values(
    template_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save default values for template fields"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Check template access and permission
    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        return RedirectResponse(
            url=f"/templates?error=not_found",
            status_code=302
        )

    # Check permission (owner, admin or editor can modify defaults)
    permission = template.get_permission_for_user(current_user.id)
    if permission not in ["owner", "admin", "editor"]:
        return RedirectResponse(
            url=f"/templates/{template_id}?error=no_permission",
            status_code=302
        )

    try:
        # Parse form data
        form = await request.form()
        default_values = {}

        for key, val in form.multi_items():
            if key.startswith("default_"):
                # Extract field name
                field_name = key[8:]  # Remove "default_" prefix

                # Handle checkboxes (HTML sends 'on' when checked)
                if val == "on":
                    default_values[field_name] = True
                elif val and val.strip():  # Only add if not empty
                    default_values[field_name] = val

        # Update template
        template.default_values = default_values if default_values else None
        db.commit()

        return RedirectResponse(
            url=f"/templates/{template_id}?success=defaults_saved",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/templates/{template_id}?error=save_failed",
            status_code=302
        )
