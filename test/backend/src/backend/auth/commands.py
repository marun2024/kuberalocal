"""
Auth domain write operations (Commands).
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.auth.jwt_auth import (
    LoginRequest,
    Token,
    create_access_token,
    extract_tenant_from_host,
    verify_password,
)
from backend.core.deps import get_public_db
from backend.sessions.service import SessionService
from backend.tenants.models import Tenant, TenantUser


async def login_command(
    login_data: LoginRequest,
    request: Request,
    public_db: Annotated[AsyncSession, Depends(get_public_db)],
) -> Token:
    """Command: Authenticate user and create JWT token."""
    # Extract tenant from subdomain (check X-Original-Host first for proxy)
    host = request.headers.get("x-original-host") or request.headers.get("host", "")
    tenant_subdomain = extract_tenant_from_host(host)

    if tenant_subdomain == "public":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please access via tenant subdomain (e.g., yourcompany.localhost:5173)"
        )

    # Get tenant from public schema
    tenant_stmt = select(Tenant).where(Tenant.subdomain == tenant_subdomain)
    tenant_result = await public_db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_subdomain}' not found"
        )

    # Get user from tenant schema using proper abstraction
    from backend.core.tenant_db import get_session_for_tenant

    async for tenant_db in get_session_for_tenant(tenant.subdomain):
        user_stmt = select(TenantUser).where(
            TenantUser.email == login_data.email,
            TenantUser.is_active
        )
        user_result = await tenant_db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token with JTI for session tracking
    access_token, expires_at, jti = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "tenant_id": tenant.id,
            "tenant_subdomain": tenant.subdomain
        }
    )

    # Create session record in tenant schema
    async for tenant_db in get_session_for_tenant(tenant.subdomain):
        session_service = SessionService(tenant_db)

        # Extract connection information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        # Create the session using service
        await session_service.create_session(
            user_id=user.id,
            token_jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # TODO: Add audit logging back once schema switching is stable
        await tenant_db.commit()

    return Token(access_token=access_token, token_type="bearer")




