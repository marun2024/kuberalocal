"""
Tenant domain schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class TenantCreate(BaseModel):
    name: str
    subdomain: str
    schema_name: str


class TenantSettingsUpdate(BaseModel):
    display_name: str | None = None
    logo_url: str | None = None


class TenantSettingsResponse(BaseModel):
    id: int
    display_name: str | None
    logo_url: str | None
    theme_settings: dict
    notification_settings: dict
    custom_metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    schema_name: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantUserCreate(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    role: str = "member"
    is_owner: bool = False
    password: str


class TenantUserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class TenantUserResponse(BaseModel):
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_owner: bool
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantUserListResponse(BaseModel):
    users: list[TenantUserResponse]
    total: int
