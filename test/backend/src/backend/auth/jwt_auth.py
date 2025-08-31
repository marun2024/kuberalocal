"""
Simple JWT-based authentication system.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


# JWT Configuration
def get_jwt_secret() -> str:
    """Get JWT secret key from settings, fail fast if not configured properly."""
    from backend.core.config import settings

    secret = settings.JWT_SECRET_KEY
    if len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be at least 32 characters long for security. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return secret

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Lazy-load the secret key to avoid import-time errors
_SECRET_KEY = None

def get_secret_key() -> str:
    """Get the JWT secret key, loading it lazily on first access."""
    global _SECRET_KEY
    if _SECRET_KEY is None:
        _SECRET_KEY = get_jwt_secret()
    return _SECRET_KEY

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    user_id: int | None = None
    tenant_id: int | None = None
    tenant_subdomain: str | None = None
    jti: str | None = None  # JWT ID for session tracking


class LoginRequest(BaseModel):
    email: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None, jti: str | None = None) -> tuple[str, datetime, str]:
    """
    Create a JWT access token with JTI for session tracking.
    Returns: (token, expiration_time, jti)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Generate JTI if not provided
    if jti is None:
        import secrets
        jti = secrets.token_urlsafe(32)

    to_encode.update({
        "exp": expire,
        "jti": jti,  # Add JWT ID for session tracking
    })

    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt, expire.replace(tzinfo=None), jti


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify and decode a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, get_secret_key(), algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        tenant_subdomain = payload.get("tenant_subdomain")
        jti = payload.get("jti")  # Extract JWT ID for session tracking

        if email is None:
            raise credentials_exception

        token_data = TokenData(
            email=email,
            user_id=user_id,
            tenant_id=tenant_id,
            tenant_subdomain=tenant_subdomain,
            jti=jti
        )
        return token_data

    except JWTError:
        raise credentials_exception from None


def extract_tenant_from_host(host: str) -> str:
    """Extract tenant subdomain from Host header."""
    if not host:
        return "public"

    # Remove port if present
    hostname = host.split(':')[0]
    parts = hostname.split('.')

    # For localhost development: tenant.localhost -> tenant
    if "localhost" in hostname and len(parts) > 1 and parts[0] != "localhost":
        return parts[0]

    # For production: tenant.domain.com -> tenant
    if len(parts) > 2:
        return parts[0]

    return "public"
