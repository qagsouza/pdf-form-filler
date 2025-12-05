"""
Web admin routes
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ...database import get_db
from ...dependencies import require_admin, get_current_user
from ...models.user import User
from ...models.group import Group, GroupMember
from ...models.permission import Role, user_roles
from ...services.auth_service import AuthService
from ...schemas.user import UserCreate
from ...utils.auth import get_password_hash, generate_user_id

router = APIRouter(prefix="/admin", tags=["web-admin"])

# Templates directory
templates = Jinja2Templates(directory="src/pdf_form_filler/web/templates")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_index(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin index page with tabs for users and groups"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    groups = db.query(Group).order_by(Group.created_at.desc()).all()
    all_roles = db.query(Role).order_by(Role.name).all()
    all_users = db.query(User).order_by(User.full_name).all()

    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "current_user": current_user,
            "users": users,
            "groups": groups,
            "all_roles": all_roles,
            "all_users": all_users
        }
    )


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users for admin"""
    users = db.query(User).order_by(User.created_at.desc()).all()

    # Get all available roles for the create user form
    all_roles = db.query(Role).order_by(Role.name).all()

    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"current_user": current_user, "users": users, "all_roles": all_roles}
    )


@router.post("/users/create")
async def create_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_approved: str = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if email exists
    existing_user = AuthService.get_user_by_email(db, email)
    if existing_user:
        return RedirectResponse(url="/admin?tab=users&error=email_exists", status_code=302)

    # Check if username exists
    existing_user = AuthService.get_user_by_username(db, username)
    if existing_user:
        return RedirectResponse(url="/admin?tab=users&error=username_exists", status_code=302)

    # Create user
    user = User(
        id=generate_user_id(),
        username=username.lower(),
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role="user",  # Default legacy value, actual permissions via RBAC
        is_active=True,
        is_verified=True,  # Admin-created users are verified by default
        is_approved=is_approved == "true",  # Checkbox value
    )

    db.add(user)
    db.flush()  # Flush to get user ID before adding roles

    # Get selected roles from form
    form = await request.form()
    selected_role_ids = form.getlist("roles")

    # Assign roles
    if selected_role_ids:
        for role_id in selected_role_ids:
            db.execute(user_roles.insert().values(user_id=user.id, role_id=role_id))
    else:
        # If no roles selected, assign viewer role by default
        viewer_role = db.query(Role).filter(Role.name == "viewer").first()
        if viewer_role:
            db.execute(user_roles.insert().values(user_id=user.id, role_id=viewer_role.id))

    db.commit()

    return RedirectResponse(url="/admin?tab=users&success=user_created", status_code=302)


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


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_page(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show edit user page"""
    if not current_user or not current_user.is_admin():
        return RedirectResponse(url="/dashboard", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)

    # Get all available roles
    all_roles = db.query(Role).order_by(Role.name).all()

    # Get user's current roles
    user_role_ids = db.query(user_roles.c.role_id).filter(user_roles.c.user_id == user_id).all()
    user_role_ids = [r[0] for r in user_role_ids]

    return templates.TemplateResponse(
        request,
        "admin/edit_user.html",
        {
            "current_user": current_user,
            "user": user,
            "all_roles": all_roles,
            "user_role_ids": user_role_ids
        }
    )


@router.post("/users/{user_id}/update")
async def update_user(
    user_id: str,
    username: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    is_active: bool = Form(False),
    is_verified: bool = Form(False),
    is_approved: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    if not current_user or not current_user.is_admin():
        return RedirectResponse(url="/dashboard", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)

    try:
        # Check if username changed and is in use
        if username != user.username:
            existing = AuthService.get_user_by_username(db, username)
            if existing and existing.id != user.id:
                return RedirectResponse(
                    url=f"/admin/users/{user_id}/edit?error=username_in_use",
                    status_code=302
                )

        # Check if email changed and is in use
        if email.lower() != user.email.lower():
            existing = AuthService.get_user_by_email(db, email)
            if existing and existing.id != user.id:
                return RedirectResponse(
                    url=f"/admin/users/{user_id}/edit?error=email_in_use",
                    status_code=302
                )

        # Update user
        user.username = username
        user.full_name = full_name
        user.email = email.lower()
        # Note: role is now managed via RBAC, not this field
        user.is_active = is_active
        user.is_verified = is_verified
        user.is_approved = is_approved

        db.commit()

        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?success=updated",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error updating user: {e}")
        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?error=update_failed",
            status_code=302
        )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset user password"""
    if not current_user or not current_user.is_admin():
        return RedirectResponse(url="/dashboard", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)

    try:
        # Verify passwords match
        if new_password != confirm_password:
            return RedirectResponse(
                url=f"/admin/users/{user_id}/edit?error=passwords_mismatch",
                status_code=302
            )

        # Update password
        user.hashed_password = AuthService.hash_password(new_password)
        db.commit()

        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?success=password_reset",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error resetting password: {e}")
        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?error=reset_failed",
            status_code=302
        )


@router.post("/users/{user_id}/update-roles")
async def update_user_roles(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user roles"""
    if not current_user or not current_user.is_admin():
        return RedirectResponse(url="/dashboard", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)

    try:
        # Get selected roles from form
        form = await request.form()
        selected_role_ids = form.getlist("roles")

        # Delete existing role assignments
        db.execute(user_roles.delete().where(user_roles.c.user_id == user_id))

        # Add new role assignments
        if selected_role_ids:
            for role_id in selected_role_ids:
                db.execute(user_roles.insert().values(user_id=user_id, role_id=role_id))

        db.commit()

        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?success=roles_updated",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error updating roles: {e}")
        return RedirectResponse(
            url=f"/admin/users/{user_id}/edit?error=roles_update_failed",
            status_code=302
        )


# Group management routes

@router.get("/groups", response_class=HTMLResponse)
def list_groups(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all groups for admin"""
    groups = db.query(Group).order_by(Group.created_at.desc()).all()

    # Get all users for the create group form
    all_users = db.query(User).order_by(User.full_name).all()

    return templates.TemplateResponse(
        request,
        "admin/groups.html",
        {"current_user": current_user, "groups": groups, "all_users": all_users}
    )


@router.post("/groups/create")
async def create_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new group (admin only)"""
    # Check if group name exists
    existing_group = db.query(Group).filter(Group.name == name).first()
    if existing_group:
        return RedirectResponse(url="/admin?tab=groups&error=group_exists", status_code=302)

    # Create group
    group = Group(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(group)
    db.flush()

    # Get selected members from form
    form = await request.form()
    selected_user_ids = form.getlist("members")

    # Add members
    for user_id in selected_user_ids:
        member = GroupMember(
            id=str(uuid.uuid4()),
            group_id=group.id,
            user_id=user_id,
            joined_at=datetime.utcnow()
        )
        db.add(member)

    db.commit()

    return RedirectResponse(url="/admin?tab=groups&success=group_created", status_code=302)


@router.get("/groups/{group_id}/edit", response_class=HTMLResponse)
def edit_group_page(
    group_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Show edit group page"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        return RedirectResponse(url="/admin/groups?error=group_not_found", status_code=302)

    # Get all users
    all_users = db.query(User).order_by(User.full_name).all()

    # Get group's current members
    member_user_ids = db.query(GroupMember.user_id).filter(GroupMember.group_id == group_id).all()
    member_user_ids = [m[0] for m in member_user_ids]

    return templates.TemplateResponse(
        request,
        "admin/edit_group.html",
        {
            "current_user": current_user,
            "group": group,
            "all_users": all_users,
            "member_user_ids": member_user_ids
        }
    )


@router.post("/groups/{group_id}/update")
async def update_group(
    group_id: str,
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update group information"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        return RedirectResponse(url="/admin/groups?error=group_not_found", status_code=302)

    try:
        # Check if name changed and is in use
        if name != group.name:
            existing = db.query(Group).filter(Group.name == name).first()
            if existing and existing.id != group.id:
                return RedirectResponse(
                    url=f"/admin/groups/{group_id}/edit?error=name_in_use",
                    status_code=302
                )

        # Update group
        group.name = name
        group.description = description
        group.updated_at = datetime.utcnow()

        db.commit()

        return RedirectResponse(
            url=f"/admin/groups/{group_id}/edit?success=updated",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error updating group: {e}")
        return RedirectResponse(
            url=f"/admin/groups/{group_id}/edit?error=update_failed",
            status_code=302
        )


@router.post("/groups/{group_id}/update-members")
async def update_group_members(
    group_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update group members"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        return RedirectResponse(url="/admin/groups?error=group_not_found", status_code=302)

    try:
        # Get selected members from form
        form = await request.form()
        selected_user_ids = form.getlist("members")

        # Delete existing memberships
        db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()

        # Add new memberships
        for user_id in selected_user_ids:
            member = GroupMember(
                id=str(uuid.uuid4()),
                group_id=group_id,
                user_id=user_id,
                joined_at=datetime.utcnow()
            )
            db.add(member)

        db.commit()

        return RedirectResponse(
            url=f"/admin/groups/{group_id}/edit?success=members_updated",
            status_code=302
        )

    except Exception as e:
        db.rollback()
        print(f"Error updating members: {e}")
        return RedirectResponse(
            url=f"/admin/groups/{group_id}/edit?error=members_update_failed",
            status_code=302
        )


@router.post("/groups/{group_id}/delete")
async def delete_group(
    group_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        db.delete(group)
        db.commit()

    return RedirectResponse(url="/admin?tab=groups&success=group_deleted", status_code=302)
