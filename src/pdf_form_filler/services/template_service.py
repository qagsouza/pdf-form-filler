"""
Template service for managing PDF templates
"""
import uuid
from typing import List, Optional, BinaryIO, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import UploadFile

from ..models.template import Template, TemplateShare, PermissionLevel
from ..models.user import User
from ..schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateShareCreate,
    TemplateShareUpdate,
)
from ..core import PDFFormFiller
from ..errors import PDFFormFillerError, InvalidFieldError
from .storage_service import StorageService


class TemplateService:
    """Service for managing templates"""

    def __init__(self, storage_service: Optional[StorageService] = None):
        """
        Initialize template service

        Args:
            storage_service: Storage service instance (creates new if not provided)
        """
        self.storage = storage_service or StorageService()

    @staticmethod
    def create_template(
        db: Session,
        user_id: str,
        template_data: TemplateCreate,
        file: UploadFile,
        storage: StorageService
    ) -> Template:
        """
        Create a new template

        Args:
            db: Database session
            user_id: Owner user ID
            template_data: Template creation data
            file: Uploaded PDF file
            storage: Storage service

        Returns:
            Created template

        Raises:
            PDFFormFillerError: If creation fails
        """
        # Generate template ID
        template_id = str(uuid.uuid4())

        try:
            # Save file
            file_path = storage.save_template(
                file.file,
                user_id,
                template_id,
                file.filename
            )

            # Extract fields from PDF
            absolute_path = storage.get_template_path(file_path)
            pdf_filler = PDFFormFiller(str(absolute_path))
            fields = pdf_filler.fields

            # Create template
            template = Template(
                id=template_id,
                name=template_data.name,
                description=template_data.description,
                owner_id=user_id,
                group_id=template_data.group_id,
                file_path=file_path,
                original_filename=file.filename,
                fields_metadata=fields,
                version=1
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            # Auto-share with group if group_id is provided
            if template_data.group_id:
                try:
                    from ..models.group import Group
                    group = db.query(Group).filter(Group.id == template_data.group_id).first()
                    if group:
                        # Check if not already shared
                        existing_share = db.query(TemplateShare).filter(
                            TemplateShare.template_id == template_id,
                            TemplateShare.group_id == template_data.group_id
                        ).first()

                        if not existing_share:
                            # Create share with editor permission by default
                            share = TemplateShare(
                                id=str(uuid.uuid4()),
                                template_id=template_id,
                                group_id=template_data.group_id,
                                shared_by_id=user_id,
                                permission=PermissionLevel.EDITOR
                            )
                            db.add(share)
                            db.commit()
                except Exception as e:
                    # Log but don't fail template creation if sharing fails
                    print(f"Warning: Failed to auto-share template with group: {e}")

            return template

        except Exception as e:
            # Clean up file if template creation fails
            try:
                storage.delete_template(file_path)
            except Exception:
                pass

            raise PDFFormFillerError(f"Failed to create template: {e}")

    @staticmethod
    def get_template(db: Session, template_id: str, user_id: str) -> Optional[Template]:
        """
        Get template by ID (only if user has access)

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user ID

        Returns:
            Template if found and accessible, None otherwise
        """
        template = db.query(Template).filter(Template.id == template_id).first()

        if not template:
            return None

        # Check if user has access
        if not template.is_accessible_by(user_id):
            return None

        return template

    @staticmethod
    def get_user_templates(db: Session, user_id: str) -> List[Template]:
        """
        Get templates owned by user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of templates
        """
        return db.query(Template).filter(Template.owner_id == user_id).all()

    @staticmethod
    def get_shared_templates(db: Session, user_id: str) -> List[Template]:
        """
        Get templates shared with user (directly or via groups)
        Excludes templates owned by the user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of shared templates
        """
        from ..models.group import GroupMember

        template_ids = set()

        # Get template IDs shared directly with user
        direct_shares = db.query(TemplateShare).filter(TemplateShare.user_id == user_id).all()
        template_ids.update([share.template_id for share in direct_shares])

        # Get user's groups
        group_memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
        group_ids = [gm.group_id for gm in group_memberships]

        # Get template IDs shared with user's groups
        if group_ids:
            group_shares = db.query(TemplateShare).filter(
                TemplateShare.group_id.in_(group_ids)
            ).all()
            template_ids.update([share.template_id for share in group_shares])

        if not template_ids:
            return []

        # Exclude templates owned by the user
        return db.query(Template).filter(
            Template.id.in_(template_ids),
            Template.owner_id != user_id
        ).all()

    @staticmethod
    def get_all_accessible_templates(db: Session, user_id: str) -> List[Template]:
        """
        Get all templates accessible by user (owned + shared)

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of templates
        """
        # Templates owned by user
        owned = db.query(Template).filter(Template.owner_id == user_id)

        # Templates shared with user
        share_ids = db.query(TemplateShare.template_id).filter(
            TemplateShare.user_id == user_id
        )
        shared = db.query(Template).filter(Template.id.in_(share_ids))

        # Combine
        return owned.union(shared).all()

    @staticmethod
    def update_template(
        db: Session,
        template_id: str,
        user_id: str,
        template_data: TemplateUpdate
    ) -> Optional[Template]:
        """
        Update template metadata

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user ID
            template_data: Update data

        Returns:
            Updated template if successful, None if not found or no permission

        Raises:
            PDFFormFillerError: If update fails
        """
        template = db.query(Template).filter(Template.id == template_id).first()

        if not template:
            return None

        # Check permission (need editor or owner)
        permission = template.get_permission_for_user(user_id)
        if permission not in ["owner", "admin", "editor"]:
            return None

        try:
            # Track if group changed
            old_group_id = template.group_id
            new_group_id = None

            # Update fields
            if template_data.name is not None:
                template.name = template_data.name
            if template_data.description is not None:
                template.description = template_data.description
            if hasattr(template_data, 'group_id'):
                new_group_id = template_data.group_id
                template.group_id = new_group_id

            db.commit()
            db.refresh(template)

            # Handle group sharing changes
            if hasattr(template_data, 'group_id') and old_group_id != new_group_id:
                try:
                    # Remove old group share if group was changed or removed
                    if old_group_id:
                        old_share = db.query(TemplateShare).filter(
                            TemplateShare.template_id == template_id,
                            TemplateShare.group_id == old_group_id
                        ).first()
                        if old_share:
                            db.delete(old_share)
                            db.commit()

                    # Add new group share if group was set
                    if new_group_id:
                        from ..models.group import Group
                        group = db.query(Group).filter(Group.id == new_group_id).first()
                        if group:
                            # Check if not already shared
                            existing_share = db.query(TemplateShare).filter(
                                TemplateShare.template_id == template_id,
                                TemplateShare.group_id == new_group_id
                            ).first()

                            if not existing_share:
                                # Create share with editor permission by default
                                share = TemplateShare(
                                    id=str(uuid.uuid4()),
                                    template_id=template_id,
                                    group_id=new_group_id,
                                    shared_by_id=user_id,
                                    permission=PermissionLevel.EDITOR
                                )
                                db.add(share)
                                db.commit()
                except Exception as e:
                    # Log but don't fail template update if sharing fails
                    print(f"Warning: Failed to update group sharing: {e}")

            return template

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to update template: {e}")

    @staticmethod
    def delete_template(
        db: Session,
        template_id: str,
        user_id: str,
        storage: StorageService
    ) -> bool:
        """
        Delete template (owner only)

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user ID
            storage: Storage service

        Returns:
            True if deleted, False if not found or no permission

        Raises:
            PDFFormFillerError: If deletion fails
        """
        template = db.query(Template).filter(Template.id == template_id).first()

        if not template:
            return False

        # Only owner can delete
        if template.owner_id != user_id:
            return False

        try:
            # Delete file
            storage.delete_template(template.file_path)

            # Delete database record (cascade will delete shares)
            db.delete(template)
            db.commit()

            return True

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to delete template: {e}")

    @staticmethod
    def get_template_fields(
        template: Template,
        storage: StorageService
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get fields from template PDF

        Args:
            template: Template model
            storage: Storage service

        Returns:
            Dictionary of fields

        Raises:
            PDFFormFillerError: If extraction fails
        """
        try:
            # Use cached fields if available
            if template.fields_metadata:
                return template.fields_metadata

            # Otherwise extract from PDF
            absolute_path = storage.get_template_path(template.file_path)
            pdf_filler = PDFFormFiller(str(absolute_path))
            return pdf_filler.fields

        except Exception as e:
            raise PDFFormFillerError(f"Failed to extract template fields: {e}")

    # Sharing methods

    @staticmethod
    def share_template(
        db: Session,
        template_id: str,
        current_user_id: str,
        share_data: TemplateShareCreate
    ) -> Optional[TemplateShare]:
        """
        Share template with another user

        Args:
            db: Database session
            template_id: Template ID
            current_user_id: Current user ID
            share_data: Share data

        Returns:
            Created share if successful, None if not found or no permission

        Raises:
            PDFFormFillerError: If sharing fails
        """
        template = db.query(Template).filter(Template.id == template_id).first()

        if not template:
            return None

        # Check permission (need admin or owner)
        permission = template.get_permission_for_user(current_user_id)
        if permission not in ["owner", "admin"]:
            return None

        # Handle user or group sharing
        if share_data.user_id:
            # Sharing with user
            target_user = db.query(User).filter(User.id == share_data.user_id).first()
            if not target_user:
                raise PDFFormFillerError("Target user not found")

            # Check if already shared
            existing_share = db.query(TemplateShare).filter(
                TemplateShare.template_id == template_id,
                TemplateShare.user_id == share_data.user_id
            ).first()

            if existing_share:
                raise PDFFormFillerError("Template already shared with this user")

            # Cannot share with self
            if share_data.user_id == template.owner_id:
                raise PDFFormFillerError("Cannot share template with owner")

        elif share_data.group_id:
            # Sharing with group
            from ..models.group import Group
            target_group = db.query(Group).filter(Group.id == share_data.group_id).first()
            if not target_group:
                raise PDFFormFillerError("Target group not found")

            # Check if already shared
            existing_share = db.query(TemplateShare).filter(
                TemplateShare.template_id == template_id,
                TemplateShare.group_id == share_data.group_id
            ).first()

            if existing_share:
                raise PDFFormFillerError("Template already shared with this group")

        else:
            raise PDFFormFillerError("Either user_id or group_id must be provided")

        try:
            # Convert permission string to enum
            permission_enum = PermissionLevel[share_data.permission.upper()]

            # Create share
            share = TemplateShare(
                id=str(uuid.uuid4()),
                template_id=template_id,
                user_id=share_data.user_id,
                group_id=share_data.group_id,
                shared_by_id=current_user_id,
                permission=permission_enum
            )

            db.add(share)
            db.commit()
            db.refresh(share)

            return share

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to share template: {e}")

    @staticmethod
    def update_share(
        db: Session,
        share_id: str,
        current_user_id: str,
        update_data: TemplateShareUpdate
    ) -> Optional[TemplateShare]:
        """
        Update share permission

        Args:
            db: Database session
            share_id: Share ID
            current_user_id: Current user ID
            update_data: Update data

        Returns:
            Updated share if successful, None if not found or no permission

        Raises:
            PDFFormFillerError: If update fails
        """
        share = db.query(TemplateShare).filter(TemplateShare.id == share_id).first()

        if not share:
            return None

        # Check permission on template
        template = db.query(Template).filter(Template.id == share.template_id).first()
        if not template:
            return None

        permission = template.get_permission_for_user(current_user_id)
        if permission not in ["owner", "admin"]:
            return None

        try:
            # Update permission
            permission_enum = PermissionLevel[update_data.permission.upper()]
            share.permission = permission_enum

            db.commit()
            db.refresh(share)

            return share

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to update share: {e}")

    @staticmethod
    def remove_share(
        db: Session,
        share_id: str,
        current_user_id: str
    ) -> bool:
        """
        Remove share

        Args:
            db: Database session
            share_id: Share ID
            current_user_id: Current user ID

        Returns:
            True if removed, False if not found or no permission

        Raises:
            PDFFormFillerError: If removal fails
        """
        share = db.query(TemplateShare).filter(TemplateShare.id == share_id).first()

        if not share:
            return False

        # Check permission on template
        template = db.query(Template).filter(Template.id == share.template_id).first()
        if not template:
            return False

        permission = template.get_permission_for_user(current_user_id)
        if permission not in ["owner", "admin"]:
            return False

        try:
            db.delete(share)
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to remove share: {e}")

    @staticmethod
    def get_template_shares(
        db: Session,
        template_id: str,
        current_user_id: str
    ) -> Optional[List[TemplateShare]]:
        """
        Get all shares for a template

        Args:
            db: Database session
            template_id: Template ID
            current_user_id: Current user ID

        Returns:
            List of shares if user has permission, None otherwise
        """
        template = db.query(Template).filter(Template.id == template_id).first()

        if not template:
            return None

        # Only owner or admin can view shares
        permission = template.get_permission_for_user(current_user_id)
        if permission not in ["owner", "admin"]:
            return None

        return db.query(TemplateShare).filter(
            TemplateShare.template_id == template_id
        ).all()
