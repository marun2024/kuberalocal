"""
Auth domain schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str = "member"
    is_owner: bool = False
    preferences: dict = {}
    metadata: dict = {}


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    preferences: dict | None = None
    metadata: dict | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_owner: bool
    is_active: bool
    preferences: dict
    custom_metadata: dict
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuthSessionResponse(BaseModel):
    id: int
    user_id: int
    provider: str
    is_active: bool
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_subdomain: str | None = None


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    tenant_subdomain: str | None = None


class AuthResponse(BaseModel):
    message: str
    user_id: str | None = None
    session_token: str | None = None


class CurrentUserResponse(BaseModel):
    """Response model for current user information."""
    user_id: int
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_owner: bool
    tenant_id: int
    tenant_name: str
    tenant_subdomain: str

