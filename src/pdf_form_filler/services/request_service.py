"""
Request service for managing form filling requests
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.request import (
    Request,
    RequestInstance,
    RequestType,
    RequestStatus,
    InstanceStatus
)
from ..models.template import Template
from ..models.user import User
from ..schemas.request import RequestCreate, RequestWithData, RequestInstanceCreate
from ..core import PDFFormFiller
from ..errors import PDFFormFillerError
from .storage_service import StorageService
from .template_service import TemplateService


class RequestService:
    """Service for managing form filling requests"""

    def __init__(self, storage_service: Optional[StorageService] = None):
        """
        Initialize request service

        Args:
            storage_service: Storage service instance
        """
        self.storage = storage_service or StorageService()

    @staticmethod
    def create_request(
        db: Session,
        user_id: str,
        request_data: RequestCreate
    ) -> Request:
        """
        Create a new request

        Args:
            db: Database session
            user_id: User ID
            request_data: Request creation data

        Returns:
            Created request

        Raises:
            PDFFormFillerError: If creation fails
        """
        # Verify template exists and user has access
        template = TemplateService.get_template(db, request_data.template_id, user_id)
        if not template:
            raise PDFFormFillerError("Template not found or access denied")

        try:
            request = Request(
                id=str(uuid.uuid4()),
                template_id=request_data.template_id,
                requester_id=user_id,
                type=RequestType.SINGLE,
                status=RequestStatus.PENDING,
                name=request_data.name,
                notes=request_data.notes
            )

            db.add(request)
            db.commit()
            db.refresh(request)

            return request

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to create request: {e}")

    @staticmethod
    def create_request_with_instance(
        db: Session,
        user_id: str,
        request_data: RequestWithData,
        storage: StorageService
    ) -> Request:
        """
        Create a request and fill it immediately

        Args:
            db: Database session
            user_id: User ID
            request_data: Request with form data
            storage: Storage service

        Returns:
            Created and processed request

        Raises:
            PDFFormFillerError: If creation or processing fails
        """
        # Verify template exists and user has access
        template = TemplateService.get_template(db, request_data.template_id, user_id)
        if not template:
            raise PDFFormFillerError("Template not found or access denied")

        try:
            # Create request
            request = Request(
                id=str(uuid.uuid4()),
                template_id=request_data.template_id,
                requester_id=user_id,
                type=RequestType.SINGLE,
                status=RequestStatus.PROCESSING,
                name=request_data.name,
                notes=request_data.notes
            )

            db.add(request)
            db.flush()  # Get request ID

            # Create instance
            instance = RequestInstance(
                id=str(uuid.uuid4()),
                request_id=request.id,
                data=request_data.data,
                recipient_email=request_data.recipient_email,
                recipient_name=request_data.recipient_name,
                status=InstanceStatus.PROCESSING
            )

            db.add(instance)
            db.flush()

            # Process the form
            try:
                RequestService._process_instance(
                    db=db,
                    instance=instance,
                    template=template,
                    storage=storage
                )

                request.status = RequestStatus.COMPLETED
                request.completed_at = datetime.utcnow()

            except Exception as e:
                # Mark as failed but don't raise
                instance.status = InstanceStatus.FAILED
                instance.error_message = str(e)
                request.status = RequestStatus.FAILED
                request.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(request)

            return request

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to create and process request: {e}")

    @staticmethod
    def _process_instance(
        db: Session,
        instance: RequestInstance,
        template: Template,
        storage: StorageService
    ) -> None:
        """
        Process a single request instance (fill the PDF)

        Args:
            db: Database session
            instance: Request instance to process
            template: Template to use
            storage: Storage service

        Raises:
            PDFFormFillerError: If processing fails
        """
        try:
            # Get template file path
            template_path = storage.get_template_path(template.file_path)

            # Create PDF filler
            filler = PDFFormFiller(str(template_path))

            # Fill the form
            filler.fill(instance.data)

            # Generate output filename
            filename = f"{instance.id}.pdf"

            # Create temp file for output
            output_path = storage.create_temp_file(".pdf")

            # Save filled PDF
            filler.save(str(output_path), flatten=True)

            # Move to filled directory
            with open(output_path, 'rb') as f:
                filled_path = storage.save_filled_pdf(
                    file=f,
                    user_id=template.owner_id,
                    request_id=instance.request_id,
                    instance_id=instance.id,
                    filename=filename
                )

            # Clean up temp file
            output_path.unlink()

            # Update instance
            instance.filled_pdf_path = filled_path
            instance.status = InstanceStatus.COMPLETED
            instance.processed_at = datetime.utcnow()

        except Exception as e:
            instance.status = InstanceStatus.FAILED
            instance.error_message = str(e)
            instance.processed_at = datetime.utcnow()
            raise PDFFormFillerError(f"Failed to process instance: {e}")

    @staticmethod
    def get_request(
        db: Session,
        request_id: str,
        user_id: str
    ) -> Optional[Request]:
        """
        Get request by ID (only if user is the requester)

        Args:
            db: Database session
            request_id: Request ID
            user_id: User ID

        Returns:
            Request if found and accessible, None otherwise
        """
        return db.query(Request).filter(
            and_(
                Request.id == request_id,
                Request.requester_id == user_id
            )
        ).first()

    @staticmethod
    def get_user_requests(
        db: Session,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Request]:
        """
        Get requests created by user

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of requests
        """
        query = db.query(Request).filter(Request.requester_id == user_id)
        query = query.order_by(Request.created_at.desc())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def delete_request(
        db: Session,
        request_id: str,
        user_id: str,
        storage: StorageService
    ) -> bool:
        """
        Delete request and all its instances

        Args:
            db: Database session
            request_id: Request ID
            user_id: User ID
            storage: Storage service

        Returns:
            True if deleted, False if not found or no permission

        Raises:
            PDFFormFillerError: If deletion fails
        """
        request = RequestService.get_request(db, request_id, user_id)

        if not request:
            return False

        try:
            # Delete all filled PDFs
            for instance in request.instances:
                if instance.filled_pdf_path:
                    try:
                        storage.delete_filled_pdf(instance.filled_pdf_path)
                    except Exception:
                        pass  # Continue even if file deletion fails

            # Delete database record (cascade will delete instances)
            db.delete(request)
            db.commit()

            return True

        except Exception as e:
            db.rollback()
            raise PDFFormFillerError(f"Failed to delete request: {e}")

    @staticmethod
    def get_request_stats(db: Session, user_id: str) -> Dict[str, int]:
        """
        Get request statistics for user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        requests = db.query(Request).filter(Request.requester_id == user_id).all()

        stats = {
            "total_requests": len(requests),
            "pending_requests": sum(1 for r in requests if r.status == RequestStatus.PENDING),
            "processing_requests": sum(1 for r in requests if r.status == RequestStatus.PROCESSING),
            "completed_requests": sum(1 for r in requests if r.status == RequestStatus.COMPLETED),
            "failed_requests": sum(1 for r in requests if r.status == RequestStatus.FAILED),
            "total_instances": sum(r.instance_count for r in requests),
            "completed_instances": sum(r.completed_count for r in requests),
            "failed_instances": sum(r.failed_count for r in requests),
        }

        return stats

    @staticmethod
    def get_instance(
        db: Session,
        instance_id: str,
        user_id: str
    ) -> Optional[RequestInstance]:
        """
        Get request instance by ID

        Args:
            db: Database session
            instance_id: Instance ID
            user_id: User ID

        Returns:
            Instance if found and accessible, None otherwise
        """
        instance = db.query(RequestInstance).filter(
            RequestInstance.id == instance_id
        ).first()

        if not instance:
            return None

        # Check if user owns the request
        if instance.request.requester_id != user_id:
            return None

        return instance
