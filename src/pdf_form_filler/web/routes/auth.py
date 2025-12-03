"""
Web authentication routes
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas.user import UserCreate
from ...services.auth_service import AuthService
from ...services.email_service import EmailService
from ...utils.auth import create_access_token, create_verification_token, verify_verification_token
from ...config import settings
from ...dependencies import get_current_user
from ...models.user import User

router = APIRouter(tags=["web-auth"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user: User = Depends(get_current_user)):
    """Show login page"""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login")
async def login_submit(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission"""
    user = AuthService.authenticate_user(db, username, password)

    if not user:
        return RedirectResponse(url="/login?error=invalid", status_code=302)

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    # Set cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax"
    )

    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, current_user: User = Depends(get_current_user)):
    """Show registration page"""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(request, "auth/register.html")


@router.post("/register")
async def register_submit(
    response: Response,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle registration form submission"""
    try:
        # Check if username already exists
        existing_user = AuthService.get_user_by_username(db, username)
        if existing_user:
            return RedirectResponse(url="/register?error=username_exists", status_code=302)

        user_data = UserCreate(
            username=username,
            email=email,
            full_name=full_name,
            password=password
        )
        user = AuthService.create_user(db, user_data)

        # Generate verification token
        verification_token = create_verification_token(user.id)
        user.email_verification_token = verification_token
        user.email_verification_sent_at = datetime.utcnow()
        db.commit()

        # Send verification email
        await EmailService.send_verification_email(
            email=user.email,
            token=verification_token,
            username=user.username
        )

        # Auto-login after registration
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.access_token_expire_minutes * 60,
            samesite="lax"
        )

        return response

    except ValueError:
        return RedirectResponse(url="/register?error=email_exists", status_code=302)


@router.get("/logout")
def logout():
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/verify-email/{token}", response_class=HTMLResponse)
async def verify_email(token: str, request: Request, db: Session = Depends(get_db)):
    """Verify user email with token"""
    # Verify token
    user_id = verify_verification_token(token)

    if not user_id:
        return templates.TemplateResponse(
            request,
            "auth/verification_failed.html",
            {"error": "Token inválido ou expirado"}
        )

    # Get user
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        return templates.TemplateResponse(
            request,
            "auth/verification_failed.html",
            {"error": "Usuário não encontrado"}
        )

    # Check if already verified
    if user.is_verified:
        return templates.TemplateResponse(
            request,
            "auth/verification_success.html",
            {"message": "Email já verificado anteriormente"}
        )

    # Mark as verified
    user.is_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    db.commit()

    return templates.TemplateResponse(
        request,
        "auth/verification_success.html",
        {"message": "Email verificado com sucesso!"}
    )


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    if current_user.is_verified:
        return RedirectResponse(url="/dashboard", status_code=302)

    # Generate new token
    verification_token = create_verification_token(current_user.id)
    current_user.email_verification_token = verification_token
    current_user.email_verification_sent_at = datetime.utcnow()
    db.commit()

    # Send email
    await EmailService.send_verification_email(
        email=current_user.email,
        token=verification_token,
        username=current_user.username
    )

    return RedirectResponse(url="/dashboard?message=verification_sent", status_code=302)
