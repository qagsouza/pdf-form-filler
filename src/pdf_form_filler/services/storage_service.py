"""
Storage service for managing files
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional
import re

from ..errors import PDFFormFillerError


class StorageService:
    """Service for managing file storage"""

    def __init__(self, base_path: str = "storage"):
        """
        Initialize storage service

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure storage directories exist"""
        directories = [
            self.base_path / "templates",
            self.base_path / "filled",
            self.base_path / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Get just the filename without path
        filename = os.path.basename(filename)

        # Remove any non-alphanumeric characters except dots, dashes, and underscores
        filename = re.sub(r'[^\w\s.-]', '', filename)

        # Replace spaces with underscores
        filename = filename.replace(' ', '_')

        # Remove multiple dots (keep only extension dot)
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            name = name.replace('.', '_')
            filename = f"{name}.{ext}"

        # Limit length
        if len(filename) > 255:
            # Keep extension
            parts = filename.rsplit('.', 1)
            if len(parts) == 2:
                name, ext = parts
                max_name_len = 255 - len(ext) - 1
                filename = f"{name[:max_name_len]}.{ext}"
            else:
                filename = filename[:255]

        return filename

    def save_template(
        self,
        file: BinaryIO,
        user_id: str,
        template_id: str,
        original_filename: str
    ) -> str:
        """
        Save template PDF file

        Args:
            file: File object to save
            user_id: Owner user ID
            template_id: Template ID
            original_filename: Original filename

        Returns:
            Relative file path

        Raises:
            PDFFormFillerError: If save fails
        """
        try:
            # Sanitize filename
            safe_filename = self.sanitize_filename(original_filename)

            # Create user directory
            user_dir = self.base_path / "templates" / user_id
            user_dir.mkdir(parents=True, exist_ok=True)

            # Create template directory
            template_dir = user_dir / template_id
            template_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = template_dir / safe_filename
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)

            # Return relative path
            return str(file_path.relative_to(self.base_path))

        except Exception as e:
            raise PDFFormFillerError(f"Failed to save template file: {e}")

    def get_template_path(self, relative_path: str) -> Path:
        """
        Get absolute path for template file

        Args:
            relative_path: Relative path from storage root

        Returns:
            Absolute path to file

        Raises:
            PDFFormFillerError: If file doesn't exist
        """
        absolute_path = self.base_path / relative_path

        if not absolute_path.exists():
            raise PDFFormFillerError(f"Template file not found: {relative_path}")

        # Security check: ensure path is within storage directory
        if not str(absolute_path.resolve()).startswith(str(self.base_path.resolve())):
            raise PDFFormFillerError("Invalid file path")

        return absolute_path

    def delete_template(self, relative_path: str) -> None:
        """
        Delete template file and its directory

        Args:
            relative_path: Relative path from storage root

        Raises:
            PDFFormFillerError: If deletion fails
        """
        try:
            file_path = self.base_path / relative_path
            template_dir = file_path.parent

            # Delete file
            if file_path.exists():
                file_path.unlink()

            # Delete directory if empty
            if template_dir.exists() and not any(template_dir.iterdir()):
                template_dir.rmdir()

                # Also delete user directory if empty
                user_dir = template_dir.parent
                if user_dir.exists() and not any(user_dir.iterdir()):
                    user_dir.rmdir()

        except Exception as e:
            raise PDFFormFillerError(f"Failed to delete template file: {e}")

    def save_filled_pdf(
        self,
        file: BinaryIO,
        user_id: str,
        request_id: str,
        instance_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save filled PDF file

        Args:
            file: File object to save
            user_id: User ID
            request_id: Request ID
            instance_id: Request instance ID
            filename: Optional filename (generated if not provided)

        Returns:
            Relative file path

        Raises:
            PDFFormFillerError: If save fails
        """
        try:
            # Generate filename if not provided
            if not filename:
                filename = f"{instance_id}.pdf"
            else:
                filename = self.sanitize_filename(filename)

            # Create directories
            filled_dir = self.base_path / "filled" / user_id / request_id
            filled_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = filled_dir / filename
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)

            # Return relative path
            return str(file_path.relative_to(self.base_path))

        except Exception as e:
            raise PDFFormFillerError(f"Failed to save filled PDF: {e}")

    def get_filled_pdf_path(self, relative_path: str) -> Path:
        """
        Get absolute path for filled PDF file

        Args:
            relative_path: Relative path from storage root

        Returns:
            Absolute path to file

        Raises:
            PDFFormFillerError: If file doesn't exist
        """
        absolute_path = self.base_path / relative_path

        if not absolute_path.exists():
            raise PDFFormFillerError(f"Filled PDF not found: {relative_path}")

        # Security check
        if not str(absolute_path.resolve()).startswith(str(self.base_path.resolve())):
            raise PDFFormFillerError("Invalid file path")

        return absolute_path

    def delete_filled_pdf(self, relative_path: str) -> None:
        """
        Delete filled PDF file

        Args:
            relative_path: Relative path from storage root

        Raises:
            PDFFormFillerError: If deletion fails
        """
        try:
            file_path = self.base_path / relative_path

            if file_path.exists():
                file_path.unlink()

        except Exception as e:
            raise PDFFormFillerError(f"Failed to delete filled PDF: {e}")

    def create_temp_file(self, extension: str = ".pdf") -> Path:
        """
        Create a temporary file

        Args:
            extension: File extension

        Returns:
            Path to temporary file
        """
        temp_dir = self.base_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_id = str(uuid.uuid4())
        return temp_dir / f"{temp_id}{extension}"

    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours

        Args:
            older_than_hours: Delete files older than this many hours

        Returns:
            Number of files deleted
        """
        import time

        temp_dir = self.base_path / "temp"
        if not temp_dir.exists():
            return 0

        current_time = time.time()
        threshold = older_than_hours * 3600
        deleted_count = 0

        for file_path in temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > threshold:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        pass

        return deleted_count

    def get_storage_info(self) -> dict:
        """
        Get storage information

        Returns:
            Dictionary with storage statistics
        """
        def get_dir_size(path: Path) -> int:
            """Calculate total size of directory"""
            total = 0
            try:
                for entry in path.rglob('*'):
                    if entry.is_file():
                        total += entry.stat().st_size
            except Exception:
                pass
            return total

        def count_files(path: Path) -> int:
            """Count files in directory"""
            count = 0
            try:
                for entry in path.rglob('*'):
                    if entry.is_file():
                        count += 1
            except Exception:
                pass
            return count

        templates_dir = self.base_path / "templates"
        filled_dir = self.base_path / "filled"
        temp_dir = self.base_path / "temp"

        return {
            "templates": {
                "size_bytes": get_dir_size(templates_dir) if templates_dir.exists() else 0,
                "file_count": count_files(templates_dir) if templates_dir.exists() else 0,
            },
            "filled": {
                "size_bytes": get_dir_size(filled_dir) if filled_dir.exists() else 0,
                "file_count": count_files(filled_dir) if filled_dir.exists() else 0,
            },
            "temp": {
                "size_bytes": get_dir_size(temp_dir) if temp_dir.exists() else 0,
                "file_count": count_files(temp_dir) if temp_dir.exists() else 0,
            },
        }
