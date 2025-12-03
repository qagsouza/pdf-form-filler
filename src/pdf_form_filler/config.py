"""
Configuration settings for the application
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App
    app_name: str = "PDF Form Filler"
    debug: bool = True

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./pdf_form_filler.db"

    # Storage
    upload_dir: Path = Path("uploads")
    templates_dir: Path = Path("storage/templates")
    filled_dir: Path = Path("storage/filled")

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 1025  # For development with mailhog/mailcatcher
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "noreply@pdfformfiller.local"
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False

    # Application URL (for email links)
    app_url: str = "http://localhost:8000"

    # Email verification
    email_verification_expire_hours: int = 24

    # Limits
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Create directories if they don't exist
settings.upload_dir.mkdir(exist_ok=True)
settings.templates_dir.mkdir(parents=True, exist_ok=True)
settings.filled_dir.mkdir(parents=True, exist_ok=True)
