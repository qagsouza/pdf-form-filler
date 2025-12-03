"""
FastAPI dependencies
"""
from typing import Optional
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models.user import User
from .services.auth_service import AuthService
from .utils.auth import decode_access_token


def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from cookie token

    Args:
        access_token: JWT token from cookie
        db: Database session

    Returns:
        Current user or None if not authenticated
    """
    if not access_token:
        return None

    # Decode token
    payload = decode_access_token(access_token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Get user from database
    user = AuthService.get_user_by_id(db, user_id)
    return user


def require_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Require authenticated and approved user

    Args:
        current_user: Current user from dependency

    Returns:
        Current user

    Raises:
        HTTPException: If user not authenticated or not approved
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval",
        )

    return current_user


def require_admin(current_user: User = Depends(require_user)) -> User:
    """
    Require admin user

    Args:
        current_user: Current user from dependency

    Returns:
        Current admin user

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
