"""
Authentication service
"""
from typing import Optional
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserCreate
from ..utils.auth import get_password_hash, verify_password, generate_user_id


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            db: Database session
            email: User email

        Returns:
            User or None
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            db: Database session
            username: Username

        Returns:
            User or None
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User or None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """
        Create a new user

        Args:
            db: Database session
            user_create: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        # Check if email exists
        existing_user = AuthService.get_user_by_email(db, user_create.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Check if username exists
        existing_user = AuthService.get_user_by_username(db, user_create.username)
        if existing_user:
            raise ValueError("Username already taken")

        # Create user
        user = User(
            id=generate_user_id(),
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=get_password_hash(user_create.password),
            is_active=True,
            is_verified=False,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password

        Args:
            db: Database session
            username: Username (not email)
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        user = AuthService.get_user_by_username(db, username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user
