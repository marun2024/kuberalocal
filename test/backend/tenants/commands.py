"""
Tenants domain write operations (Commands).
"""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_auth import get_password_hash
from backend.core.audit import log_audit
from backend.core.deps import (
    BaseContext,
    get_base_context,
    get_public_db,
    get_tenant_db,
)
from backend.tenants.models import Tenant, TenantSettings, TenantStatus, TenantUser
from backend.tenants.schemas import (
    TenantSettingsUpdate,
    TenantUserCreate,
    TenantUserUpdate,
)

if TYPE_CHECKING:
    from backend.tenants.router import TenantCreate


async def create_tenant_command(
    tenant_data: "TenantCreate",
    db: Annotated[AsyncSession, Depends(get_public_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> Tenant:
    """Command: Create a new tenant."""
    tenant = Tenant(
        name=tenant_data.name,
        subdomain=tenant_data.subdomain,
        schema_name=tenant_data.schema_name,
        status=TenantStatus.ACTIVE,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return tenant


async def update_tenant_settings_command(
    settings_data: TenantSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantSettings:
    """Command: Update tenant settings (tenant admin accessible)."""
    # Check if user is admin/owner
    if not (context.request_user.is_owner or context.request_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update tenant settings"
        )

    from sqlmodel import select

    # Get or create tenant settings
    result = await db.execute(select(TenantSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = TenantSettings()
        db.add(settings)

    # Store changes for audit
    changes = {}

    # Update fields
    if settings_data.display_name is not None:
        changes["display_name"] = {"old": settings.display_name, "new": settings_data.display_name}
        settings.display_name = settings_data.display_name

    if settings_data.logo_url is not None:
        changes["logo_url"] = {"old": settings.logo_url, "new": settings_data.logo_url}
        settings.logo_url = settings_data.logo_url

    # Audit log
    if changes:
        await log_audit(
            session=db,
            user_id=context.request_user.user_id,
            action="tenant_settings_updated",
            resource_type="tenant_settings",
            resource_id=str(settings.id) if settings.id else "new",
            changes=changes
        )

    await db.commit()
    
    # Don't refresh - we already have the updated data and it causes search path issues
    return settings


async def create_tenant_user_command(
    user_data: TenantUserCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantUser:
    """Command: Create a new tenant user."""
    # Check if user is admin
    if not (context.request_user.is_owner or context.request_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )

    # Check if email already exists
    from sqlmodel import select
    existing_user = await db.execute(select(TenantUser).where(TenantUser.email == user_data.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Create user
    user = TenantUser(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_owner=user_data.is_owner,
        password_hash=password_hash,
        is_active=True
    )

    db.add(user)
    await db.flush()

    # Audit log
    await log_audit(
        session=db,
        user_id=context.request_user.user_id,
        action="user_created",
        resource_type="tenant_user",
        resource_id=str(user.id),
        changes={
            "email": user_data.email,
            "role": user_data.role,
            "is_owner": user_data.is_owner
        }
    )

    await db.commit()

    return user


async def update_tenant_user_command(
    user_id: int,
    user_data: TenantUserUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantUser | None:
    """Command: Update a tenant user."""
    # Check if user is admin
    if not (context.request_user.is_owner or context.request_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )

    # Get user
    from sqlmodel import select
    result = await db.execute(select(TenantUser).where(TenantUser.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Can't update own owner status or role
    if user.id == context.request_user.user_id and user_data.role is not None and user_data.role != user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Store changes for audit
    changes = {}

    # Update fields
    if user_data.first_name is not None:
        changes["first_name"] = {"old": user.first_name, "new": user_data.first_name}
        user.first_name = user_data.first_name

    if user_data.last_name is not None:
        changes["last_name"] = {"old": user.last_name, "new": user_data.last_name}
        user.last_name = user_data.last_name

    if user_data.role is not None:
        changes["role"] = {"old": user.role, "new": user_data.role}
        user.role = user_data.role

    if user_data.is_active is not None:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active

    # Audit log
    if changes:
        await log_audit(
            session=db,
            user_id=context.request_user.user_id,
            action="user_updated",
            resource_type="tenant_user",
            resource_id=str(user.id),
            changes=changes
        )

    await db.commit()
    await db.refresh(user)

    return user


async def delete_tenant_user_command(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> bool:
    """Command: Delete a tenant user."""
    # Check if user is admin
    if not (context.request_user.is_owner or context.request_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )

    # Get user
    from sqlmodel import select
    result = await db.execute(select(TenantUser).where(TenantUser.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Can't delete self
    if user.id == context.request_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    # Can't delete tenant owner
    if user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tenant owner"
        )

    # Audit log
    await log_audit(
        session=db,
        user_id=context.request_user.user_id,
        action="user_deleted",
        resource_type="tenant_user",
        resource_id=str(user.id),
        changes={
            "email": user.email,
            "role": user.role
        }
    )

    await db.delete(user)
    await db.commit()

    return True
