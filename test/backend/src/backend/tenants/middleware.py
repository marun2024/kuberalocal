"""
Tenant context middleware for multi-tenant operations.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from backend.auth.jwt_auth import TokenData, verify_token
from backend.core.tenant_db import set_tenant_context


async def set_tenant_context_middleware(
    token_data: Annotated[TokenData, Depends(verify_token)],
) -> TokenData:
    """
    Middleware to set tenant context from JWT token.
    This must run before any tenant-scoped operations.
    """
    if token_data.tenant_subdomain:
        await set_tenant_context(f"tenant_{token_data.tenant_subdomain}")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token - missing tenant context",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data
