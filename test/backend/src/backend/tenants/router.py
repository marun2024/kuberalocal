"""
Tenants domain API routes using CQRS pattern.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.tenants.commands import (
    create_tenant_command,
    create_tenant_user_command,
    delete_tenant_user_command,
    update_tenant_settings_command,
    update_tenant_user_command,
)
from backend.tenants.models import Tenant, TenantSettings, TenantStatus, TenantUser
from backend.tenants.queries import (
    get_tenant_query,
    get_tenant_settings_query,
    get_tenant_user_query,
    list_tenant_users_query,
)
from backend.tenants.schemas import (
    TenantSettingsResponse,
    TenantSettingsUpdate,
    TenantUserCreate,
    TenantUserListResponse,
    TenantUserResponse,
    TenantUserUpdate,
)

# Tenant router
tenant_router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
)

# Invitation router
invitation_router = APIRouter(
    prefix="/invitations",
    tags=["invitations"],
)


# Schemas
class TenantCreate(BaseModel):
    name: str
    subdomain: str
    schema_name: str


class TenantResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    schema_name: str
    status: TenantStatus
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class InvitationResponse(BaseModel):
    tenant_name: str
    tenant_subdomain: str
    email: str
    role: str
    expires_at: str
    valid: bool


class AcceptInvitationRequest(BaseModel):
    token: str


# Tenant endpoints
@tenant_router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant_endpoint(
    tenant_id: int,
    tenant: Annotated[Tenant | None, Depends(get_tenant_query)],
) -> TenantResponse:
    """Get tenant by ID."""
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse.model_validate(tenant)


@tenant_router.post("/", response_model=TenantResponse)
async def create_tenant_endpoint(
    tenant_data: TenantCreate,
    tenant: Annotated[Tenant, Depends(create_tenant_command)],
) -> TenantResponse:
    """Create a new tenant."""
    return TenantResponse.model_validate(tenant)


@tenant_router.get("/settings", response_model=TenantSettingsResponse)
async def get_tenant_settings_endpoint(
    settings: Annotated[TenantSettings | None, Depends(get_tenant_settings_query)]
) -> TenantSettingsResponse:
    """Get current tenant settings."""
    if not settings:
        # Return default settings if none exist
        from backend.core.base_models import utc_now
        now = utc_now()
        # Create a dictionary to avoid SQLModel validation issues
        default_settings = {
            "id": 1,  # Use 1 instead of 0 for default
            "display_name": None,
            "logo_url": None,
            "theme_settings": {},
            "notification_settings": {},
            "custom_metadata": {},
            "created_at": now,
            "updated_at": now
        }
        return TenantSettingsResponse.model_validate(default_settings)
    return TenantSettingsResponse.model_validate(settings)


@tenant_router.patch("/settings", response_model=TenantSettingsResponse)
async def update_tenant_settings_endpoint(
    settings_data: TenantSettingsUpdate,
    settings: Annotated[TenantSettings, Depends(update_tenant_settings_command)]
) -> TenantSettingsResponse:
    """Update tenant settings (admin only)."""
    return TenantSettingsResponse.model_validate(settings)


# Tenant Users router
users_router = APIRouter(
    prefix="/users",
    tags=["tenant-users"],
)


# Tenant User endpoints
@users_router.get("", response_model=TenantUserListResponse)
async def list_tenant_users_endpoint(
    users_data: Annotated[TenantUserListResponse, Depends(list_tenant_users_query)]
) -> TenantUserListResponse:
    """List all users in the current tenant."""
    return users_data


@users_router.post("", response_model=TenantUserResponse)
async def create_tenant_user_endpoint(
    user_data: TenantUserCreate,
    user: Annotated[TenantUser, Depends(create_tenant_user_command)]
) -> TenantUserResponse:
    """Create a new tenant user."""
    return TenantUserResponse.model_validate(user)


@users_router.get("/{user_id}", response_model=TenantUserResponse)
async def get_tenant_user_endpoint(
    user_id: int,
    user: Annotated[TenantUser | None, Depends(get_tenant_user_query)]
) -> TenantUserResponse:
    """Get tenant user by ID."""
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TenantUserResponse.model_validate(user)


@users_router.patch("/{user_id}", response_model=TenantUserResponse)
async def update_tenant_user_endpoint(
    user_id: int,
    user_update: TenantUserUpdate,
    user: Annotated[TenantUser | None, Depends(update_tenant_user_command)]
) -> TenantUserResponse:
    """Update tenant user by ID."""
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TenantUserResponse.model_validate(user)


@users_router.delete("/{user_id}")
async def delete_tenant_user_endpoint(
    user_id: int,
    success: Annotated[bool, Depends(delete_tenant_user_command)]
) -> dict[str, str]:
    """Delete tenant user by ID."""
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# Main router combining all
router = APIRouter()
router.include_router(tenant_router)
router.include_router(users_router)
router.include_router(invitation_router)
