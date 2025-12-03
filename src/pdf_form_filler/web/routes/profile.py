"""
Web routes for user profile management
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User
from ...services.auth_service import AuthService

router = APIRouter(tags=["web-profile"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show user profile page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        http_request,
        "profile.html",
        {"current_user": current_user}
    )


@router.post("/profile/update")
async def update_profile(
    http_request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        # Check if email changed
        email_changed = email.lower() != current_user.email.lower()

        # If email changed, check if it's already in use
        if email_changed:
            existing_user = AuthService.get_user_by_email(db, email)
            if existing_user and existing_user.id != current_user.id:
                return RedirectResponse(
                    url="/profile?error=email_in_use",
                    status_code=302
                )

        # Update user
        current_user.full_name = full_name

        # If email changed, mark as unverified and send new verification
        if email_changed:
            current_user.email = email.lower()
            current_user.is_verified = False

            # Generate new verification token
            from ...services.auth_service import AuthService
            token = AuthService.generate_verification_token(current_user, db)

            # Send verification email
            from ...services.email_service import EmailService
            try:
                await EmailService.send_verification_email(
                    email=current_user.email,
                    token=token,
                    username=current_user.username
                )
            except Exception as e:
                print(f"Failed to send verification email: {e}")

        db.commit()

        if email_changed:
            return RedirectResponse(
                url="/profile?success=email_changed",
                status_code=302
            )
        else:
            return RedirectResponse(
                url="/profile?success=profile_updated",
                status_code=302
            )

    except Exception as e:
        db.rollback()
        print(f"Error updating profile: {e}")
        return RedirectResponse(
            url="/profile?error=update_failed",
            status_code=302
        )


@router.post("/profile/change-password")
async def change_password(
    http_request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        # Verify current password
        if not AuthService.verify_password(current_password, current_user.hashed_password):
            return RedirectResponse(
                url="/profile?error=wrong_password",
                status_code=302
            )

        # Verify new passwords match
        if new_password != confirm_password:
            return RedirectResponse(
                url="/profile?error=passwords_mismatch",
                status_code=302
            )

        # Update password
        current_user.hashed_password = AuthService.hash_password(new_password)
        db.commit()

        return RedirectResponse(
            url="/profile?success=password_changed",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error changing password: {e}")
        return RedirectResponse(
            url="/profile?error=update_failed",
            status_code=302
        )
