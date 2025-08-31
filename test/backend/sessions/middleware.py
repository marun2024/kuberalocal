"""
Session validation middleware for checking token revocation status.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from backend.auth.jwt_auth import TokenData
from backend.sessions.service import SessionService
from backend.tenants.deps import (
    AuthenticatedTenantContext,
    get_authenticated_tenant_context,
)

security = HTTPBearer()


async def validate_session(
    context: Annotated[AuthenticatedTenantContext, Depends(get_authenticated_tenant_context)],
) -> TokenData:
    """
    Middleware to validate that a JWT token's session is still active.
    This should be used as a dependency for protected endpoints.
    Uses composite dependency to ensure proper middleware chain execution.
    """
    # JTI is required for session management
    if not context.jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format - session tracking required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if session is valid using tenant database session
    session_service = SessionService(context.db_session)
    session = await session_service.validate_session(context.jti)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return context.token_data
