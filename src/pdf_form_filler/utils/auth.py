"""
Authentication utilities
"""
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Optional

# Suppress bcrypt version warning (compatibility issue between passlib 1.7.4 and bcrypt 5.0)
warnings.filterwarnings("ignore", message=".*bcrypt.*")

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode JWT access token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_user_id() -> str:
    """
    Generate a unique user ID

    Returns:
        UUID as string
    """
    return str(uuid.uuid4())


def generate_verification_token() -> str:
    """
    Generate a secure email verification token

    Returns:
        Random token string
    """
    return str(uuid.uuid4())


def create_verification_token(user_id: str) -> str:
    """
    Create a JWT token for email verification

    Args:
        user_id: User ID to encode

    Returns:
        Encoded JWT token
    """
    from datetime import datetime, timedelta

    expire = datetime.utcnow() + timedelta(hours=settings.email_verification_expire_hours)

    to_encode = {
        "sub": user_id,
        "type": "email_verification",
        "exp": expire
    }

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_verification_token(token: str) -> Optional[str]:
    """
    Verify and decode email verification token

    Args:
        token: JWT token to verify

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # Check token type
        if payload.get("type") != "email_verification":
            return None

        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
