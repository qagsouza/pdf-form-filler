"""
Web routes for request management (form filling)
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User
from ...schemas.request import RequestWithData
from ...services.request_service import RequestService
from ...services.storage_service import StorageService
from ...services.template_service import TemplateService
from ...errors import PDFFormFillerError

router = APIRouter(tags=["web-requests"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")

# Initialize services
storage_service = StorageService()
request_service = RequestService(storage_service)


@router.get("/requests", response_class=HTMLResponse)
def requests_page(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show requests list page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Get user's requests
    requests_list = RequestService.get_user_requests(db, current_user.id, limit=50)

    # Enrich with template names
    requests_data = []
    for req in requests_list:
        template_name = req.template.name if req.template else "Template desconhecido"
        requests_data.append({
            "request": req,
            "template_name": template_name
        })

    # Get stats
    stats = RequestService.get_request_stats(db, current_user.id)

    return templates.TemplateResponse(
        http_request,
        "requests/list.html",
        {
            "requests": requests_data,
            "stats": stats,
            "current_user": current_user
        }
    )


@router.get("/requests/{request_id}", response_class=HTMLResponse)
def request_details(
    request_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show request details page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    req = RequestService.get_request(db, request_id, current_user.id)

    if not req:
        return RedirectResponse(url="/requests?error=not_found", status_code=302)

    template_name = req.template.name if req.template else "Template desconhecido"

    return templates.TemplateResponse(
        http_request,
        "requests/details.html",
        {
            "req": req,
            "template_name": template_name,
            "current_user": current_user
        }
    )


@router.get("/fill/{template_id}", response_class=HTMLResponse)
def fill_form_page(
    template_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show form filling page for a template"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Get template
    template = TemplateService.get_template(db, template_id, current_user.id)

    if not template:
        return RedirectResponse(url="/templates?error=not_found", status_code=302)

    # Get fields
    try:
        fields = TemplateService.get_template_fields(template, storage_service)
    except PDFFormFillerError:
        fields = {}

    return templates.TemplateResponse(
        http_request,
        "requests/fill.html",
        {
            "template": template,
            "fields": fields,
            "current_user": current_user
        }
    )


@router.post("/fill/{template_id}")
async def submit_fill_form(
    template_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process form submission"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        # Parse form data
        form = await http_request.form()
        data = {}

        for key, val in form.multi_items():
            if key in ["template_id", "request_name", "request_notes"]:
                continue

            # Handle checkboxes (HTML sends 'on' when checked)
            if val == "on":
                data[key] = True
            elif isinstance(val, list):
                data[key] = val
            else:
                # Only add if not empty
                if val and val.strip():
                    data[key] = val

        # Get optional fields
        request_name = form.get("request_name", "").strip() or None
        request_notes = form.get("request_notes", "").strip() or None

        # Create request
        request_data = RequestWithData(
            template_id=template_id,
            name=request_name,
            notes=request_notes,
            data=data
        )

        req = RequestService.create_request_with_instance(
            db=db,
            user_id=current_user.id,
            request_data=request_data,
            storage=storage_service
        )

        return RedirectResponse(
            url=f"/requests/{req.id}?success=created",
            status_code=302
        )

    except PDFFormFillerError as e:
        return RedirectResponse(
            url=f"/fill/{template_id}?error=processing_failed",
            status_code=302
        )


@router.post("/requests/{request_id}/delete")
async def delete_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a request"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        deleted = RequestService.delete_request(
            db=db,
            request_id=request_id,
            user_id=current_user.id,
            storage=storage_service
        )

        if not deleted:
            return RedirectResponse(
                url="/requests?error=delete_failed",
                status_code=302
            )

        return RedirectResponse(
            url="/requests?success=deleted",
            status_code=302
        )

    except PDFFormFillerError:
        return RedirectResponse(
            url="/requests?error=delete_failed",
            status_code=302
        )


@router.get("/requests/{request_id}/download/{instance_id}")
async def download_filled_pdf(
    request_id: str,
    instance_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download filled PDF"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Get instance
    instance = RequestService.get_instance(db, instance_id, current_user.id)

    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if not instance.filled_pdf_path:
        raise HTTPException(status_code=404, detail="Filled PDF not available")

    try:
        file_path = storage_service.get_filled_pdf_path(instance.filled_pdf_path)

        # Generate filename
        req = instance.request
        template_name = req.template.name if req.template else "form"
        safe_name = template_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_filled.pdf"

        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/pdf"
        )

    except PDFFormFillerError as e:
        raise HTTPException(status_code=404, detail=str(e))
