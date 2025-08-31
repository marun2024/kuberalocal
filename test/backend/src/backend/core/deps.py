"""
Core dependency injection providers for FastAPI routes.
These handle database sessions, tenant context, and authentication.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session_maker


@dataclass
class TenantInfo:
    """Tenant information for the request."""
    tenant_id: int
    name: str
    subdomain: str
    schema_name: str


@dataclass
class RequestUser:
    """User making the request with tenant info."""
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_owner: bool
    tenant: TenantInfo


@dataclass
class AuthorizationContext:
    """Authorization/permissions for the request."""
    permissions: set[str]
    can_admin: bool
    can_write: bool


@dataclass
class BaseContext:
    """Base context for all requests."""
    request_user: RequestUser
    authorization: AuthorizationContext
    ip_address: str | None = None
    user_agent: str | None = None


async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session with public schema access."""
    async with async_session_maker() as session:
        await session.execute(text("SET search_path TO public"))
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async with async_session_maker() as session:
        yield session



def get_tenant_schema(request: Request) -> str:
    """
    Get the current tenant schema name for database operations.
    This only exposes the schema name, not the full tenant object.
    """
    if not hasattr(request.state, "tenant") or not request.state.tenant:
        raise HTTPException(status_code=400, detail="No tenant context")
    return request.state.tenant.schema_name


def require_tenant_context(request: Request) -> None:
    """
    Verify that request has valid tenant context.
    Raises exception if not - use this for tenant-scoped endpoints.
    """
    if not hasattr(request.state, "tenant") or not request.state.tenant:
        raise HTTPException(
            status_code=400, detail="This endpoint requires tenant context"
        )


async def get_request_user(
    request: Request,
    public_db: Annotated[AsyncSession, Depends(get_public_db)]
) -> RequestUser:
    """
    Get current authenticated user as RequestUser object.
    """
    import logging

    from fastapi import status
    from jose import JWTError, jwt
    from sqlmodel import select

    from backend.tenants.models import Tenant, TenantUser

    logger = logging.getLogger(__name__)
    logger.debug(f"get_request_user called for {request.method} {request.url}")

    # Extract JWT token from Authorization header
    auth_header = request.headers.get("authorization")
    logger.debug(f"Auth header present: {bool(auth_header)}")

    if not auth_header or not auth_header.startswith("Bearer "):
        logger.debug("Missing or invalid authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]
    logger.debug(f"Token extracted, length: {len(token)}")

    # Decode JWT token
    try:
        from backend.auth.jwt_auth import ALGORITHM, get_secret_key
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")

        logger.debug("Token payload decoded successfully")

        if email is None or user_id is None or tenant_id is None:
            logger.debug("Invalid token payload - missing required fields")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    # Get tenant details from public schema
    logger.debug("Looking up tenant from token")
    tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
    tenant_result = await public_db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        logger.debug("Tenant not found for token")
        raise HTTPException(status_code=401, detail="Invalid tenant in token")

    logger.debug("Tenant found successfully")

    # Domain validation: Check if subdomain in URL matches tenant in token
    from backend.core.middleware import extract_tenant_subdomain
    host = request.headers.get("x-original-host") or request.headers.get("host", "")
    request_subdomain = extract_tenant_subdomain(host)

    if request_subdomain != "public" and request_subdomain != tenant.subdomain:
        logger.warning("Domain mismatch: URL subdomain does not match token tenant")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid tenant domain"
        )

    logger.debug("Domain validation passed")

    # Get user details from tenant schema using a separate session
    async with async_session_maker() as tenant_session:
        schema_name = f"tenant_{tenant.subdomain}"
        # Validate schema name contains only safe characters
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
            raise HTTPException(status_code=400, detail="Invalid schema name")

        logger.debug("Setting search path to tenant schema")
        # Set search path with validated schema name
        await tenant_session.execute(text(f"SET search_path TO {schema_name}"))

        # Check current search path
        await tenant_session.execute(text("SHOW search_path"))
        logger.debug("Search path configured")

        # Check if schema exists
        schema_exists_result = await tenant_session.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema)"),
            {"schema": schema_name}
        )
        schema_exists = schema_exists_result.scalar()
        logger.debug(f"Schema exists: {schema_exists}")

        # Check if table exists in schema
        table_exists_result = await tenant_session.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = 'tenant_users')"),
            {"schema": schema_name}
        )
        table_exists = table_exists_result.scalar()
        logger.debug(f"Table tenant_users exists: {table_exists}")

        user_stmt = select(TenantUser).where(TenantUser.id == user_id)
        logger.debug("Executing user lookup query")
        user_result = await tenant_session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            logger.debug("User not found in tenant schema")
            raise HTTPException(status_code=401, detail="User not found")

        logger.debug("User found successfully")

    # Build tenant info
    tenant_info = TenantInfo(
        tenant_id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        schema_name=f"tenant_{tenant.subdomain}"
    )

    # Build request user
    return RequestUser(
        user_id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_owner=user.is_owner,
        tenant=tenant_info
    )


async def get_authorization_context(
    request_user: Annotated[RequestUser, Depends(get_request_user)]
) -> AuthorizationContext:
    """
    Build authorization context from user info.
    TODO: Replace with middleware-based permissions loading.
    """
    # Basic role-based permissions for MVP
    permissions = set()
    can_admin = request_user.is_owner or request_user.role == "admin"
    can_write = can_admin or request_user.role in ["manager", "editor"]

    if can_admin:
        permissions.update(["admin", "write", "read"])
    elif can_write:
        permissions.update(["write", "read"])
    else:
        permissions.add("read")

    return AuthorizationContext(
        permissions=permissions,
        can_admin=can_admin,
        can_write=can_write
    )


async def get_base_context(
    request: Request,
    request_user: Annotated[RequestUser, Depends(get_request_user)],
    authorization: Annotated[AuthorizationContext, Depends(get_authorization_context)]
) -> BaseContext:
    """
    Build base context for all requests, including audit metadata.
    """
    # Extract client IP address (handle proxies)
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    if ip_address and "," in ip_address:
        # Take first IP if multiple (proxy chain)
        ip_address = ip_address.split(",")[0].strip()

    # Extract user agent
    user_agent = request.headers.get("user-agent")

    return BaseContext(
        request_user=request_user,
        authorization=authorization,
        ip_address=ip_address,
        user_agent=user_agent
    )


async def get_tenant_db(
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> AsyncGenerator[AsyncSession, None]:
    """Database session with tenant context enforced."""
    import re
    from backend.core.tenant_db import set_tenant_context
    
    # Set the tenant context for this request
    await set_tenant_context(context.request_user.tenant.schema_name)
    
    # Create session with tenant context - simplified approach
    async with async_session_maker() as session:
        schema_name = context.request_user.tenant.schema_name
        # Validate schema name contains only safe characters
        if not re.match(r'^tenant_[a-zA-Z][a-zA-Z0-9_]*$', schema_name):
            raise HTTPException(status_code=400, detail="Invalid schema name")
        
        # Set search path with proper PostgreSQL function - use true for session-level setting
        await session.execute(
            text("SELECT set_config('search_path', quote_ident(:schema_name), true)"),
            {"schema_name": schema_name}
        )
        
        # Verify search path was set
        result = await session.execute(text("SHOW search_path"))
        current_path = result.scalar()
        # Uncomment for debugging: print(f"DEBUG: Search path set to: {current_path}")
        
        yield session
