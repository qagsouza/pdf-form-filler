"""
Permission checking utilities and decorators
"""
from functools import wraps
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import get_current_user
from .models.user import User


class PermissionDenied(HTTPException):
    """Exception raised when user doesn't have required permission"""
    
    def __init__(self, permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required permission: {permission}"
        )


def require_permission(permission: str):
    """
    Dependency that requires user to have a specific permission
    
    Usage:
        @router.get("/templates")
        def list_templates(
            user: User = Depends(require_permission("template.read"))
        ):
            ...
    
    Args:
        permission: Permission name (e.g., "template.create")
    
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        if not current_user.has_permission(permission):
            raise PermissionDenied(permission)
        
        return current_user
    
    return permission_checker


def require_any_permission(*permissions: str):
    """
    Dependency that requires user to have ANY of the specified permissions
    
    Usage:
        @router.get("/templates")
        def list_templates(
            user: User = Depends(require_any_permission("template.read", "template.create"))
        ):
            ...
    
    Args:
        *permissions: List of permission names
    
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        has_any = any(current_user.has_permission(perm) for perm in permissions)
        
        if not has_any:
            raise PermissionDenied(", ".join(permissions))
        
        return current_user
    
    return permission_checker


def require_all_permissions(*permissions: str):
    """
    Dependency that requires user to have ALL of the specified permissions
    
    Usage:
        @router.post("/templates/{id}/share")
        def share_template(
            user: User = Depends(require_all_permissions("template.read", "template.share"))
        ):
            ...
    
    Args:
        *permissions: List of permission names
    
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        missing_perms = [
            perm for perm in permissions 
            if not current_user.has_permission(perm)
        ]
        
        if missing_perms:
            raise PermissionDenied(", ".join(missing_perms))
        
        return current_user
    
    return permission_checker


def check_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission
    
    Args:
        user: User object
        permission: Permission name
    
    Returns:
        True if user has permission
    """
    return user.has_permission(permission)


def check_any_permission(user: User, *permissions: str) -> bool:
    """Check if user has any of the specified permissions"""
    return any(user.has_permission(perm) for perm in permissions)


def check_all_permissions(user: User, *permissions: str) -> bool:
    """Check if user has all of the specified permissions"""
    return all(user.has_permission(perm) for perm in permissions)
