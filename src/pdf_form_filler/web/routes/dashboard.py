"""
Web dashboard routes
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...dependencies import get_current_user
from ...models.user import User

router = APIRouter(tags=["web-dashboard"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, current_user: User = Depends(get_current_user)):
    """Home page - redirect based on auth status"""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Show user dashboard"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Check if user is approved
    if not current_user.is_approved:
        return templates.TemplateResponse(
            request,
            "pending_approval.html",
            {"current_user": current_user}
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"current_user": current_user}
    )


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, current_user: User = Depends(get_current_user)):
    """Show user profile"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "profile.html",
        {"current_user": current_user}
    )
