"""
Tenant extraction utilities for multi-tenant routing.
"""

from collections.abc import Callable

from fastapi import Request, Response
from sqlmodel import select

from backend.core.database import async_session_maker
from backend.tenants.models import Tenant


def extract_tenant_subdomain(host: str) -> str:
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


async def set_tenant_context(request: Request) -> None:
    """Extract tenant from request and set on request state."""
    # Extract tenant from Host header (check X-Original-Host first for proxy support)
    host = request.headers.get("x-original-host") or request.headers.get("host", "")
    tenant_subdomain = extract_tenant_subdomain(host)

    # Set tenant context on request state
    request.state.tenant = None

    if tenant_subdomain != "public":
        # Get tenant from database
        async with async_session_maker() as session:
            tenant_stmt = select(Tenant).where(Tenant.subdomain == tenant_subdomain)
            result = await session.execute(tenant_stmt)
            tenant = result.scalar_one_or_none()

            if tenant:
                # Store tenant info in request state
                request.state.tenant = tenant



async def tenant_middleware(request: Request, call_next: Callable) -> Response:
    """Function-based tenant middleware."""
    await set_tenant_context(request)
    response = await call_next(request)
    return response
