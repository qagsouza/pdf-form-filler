"""
Web admin routes
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...database import get_db
from ...dependencies import require_admin
from ...models.user import User
from ...services.auth_service import AuthService
from ...schemas.user import UserCreate
from ...utils.auth import get_password_hash, generate_user_id

router = APIRouter(prefix="/admin", tags=["web-admin"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users for admin"""
    users = db.query(User).order_by(User.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"current_user": current_user, "users": users}
    )


@router.post("/users/create")
async def create_user(
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    is_approved: str = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if email exists
    existing_user = AuthService.get_user_by_email(db, email)
    if existing_user:
        return RedirectResponse(url="/admin/users?error=email_exists", status_code=302)

    # Check if username exists
    existing_user = AuthService.get_user_by_username(db, username)
    if existing_user:
        return RedirectResponse(url="/admin/users?error=username_exists", status_code=302)

    # Create user
    user = User(
        id=generate_user_id(),
        username=username.lower(),
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=role,
        is_active=True,
        is_verified=True,  # Admin-created users are verified by default
        is_approved=is_approved == "true",  # Checkbox value
    )

    db.add(user)
    db.commit()

    return RedirectResponse(url="/admin/users?success=user_created", status_code=302)


@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve a user"""
    user = AuthService.get_user_by_id(db, user_id)
    if user:
        user.is_approved = True
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/revoke")
async def revoke_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Revoke user approval"""
    user = AuthService.get_user_by_id(db, user_id)
    if user and user.id != current_user.id:  # Can't revoke own approval
        user.is_approved = False
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/toggle-admin")
async def toggle_admin(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle user admin status"""
    user = AuthService.get_user_by_id(db, user_id)
    if user and user.id != current_user.id:  # Can't change own role
        user.role = "user" if user.is_admin() else "admin"
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user"""
    user = AuthService.get_user_by_id(db, user_id)
    if user and user.id != current_user.id:  # Can't delete self
        db.delete(user)
        db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)
