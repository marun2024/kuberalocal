"""
Tenants domain read operations (Queries).
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.core.deps import (
    BaseContext,
    get_base_context,
    get_public_db,
    get_tenant_db,
)
from backend.tenants.models import Tenant, TenantSettings, TenantUser
from backend.tenants.schemas import TenantUserListResponse, TenantUserResponse


async def get_tenant_query(
    tenant_id: int,
    db: Annotated[AsyncSession, Depends(get_public_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> Tenant | None:
    """Query: Get tenant by ID."""
    statement = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_tenant_by_subdomain_query(
    subdomain: str,
    db: Annotated[AsyncSession, Depends(get_public_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> Tenant | None:
    """Query: Get tenant by subdomain."""
    statement = select(Tenant).where(Tenant.subdomain == subdomain)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def list_tenants_query(
    db: Annotated[AsyncSession, Depends(get_public_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> list[Tenant]:
    """Query: List all tenants."""
    statement = select(Tenant)
    result = await db.execute(statement)
    return list(result.scalars().all())


async def list_tenant_users_query(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantUserListResponse:
    """Query: List all users in the current tenant."""
    statement = select(TenantUser).order_by(TenantUser.created_at.desc())
    result = await db.execute(statement)
    users = list(result.scalars().all())

    return TenantUserListResponse(
        users=[TenantUserResponse.model_validate(user) for user in users],
        total=len(users)
    )


async def get_tenant_user_query(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantUser | None:
    """Query: Get tenant user by ID."""
    statement = select(TenantUser).where(TenantUser.id == user_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_tenant_settings_query(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> TenantSettings | None:
    """Query: Get current tenant settings."""
    statement = select(TenantSettings)
    result = await db.execute(statement)
    return result.scalar_one_or_none()
