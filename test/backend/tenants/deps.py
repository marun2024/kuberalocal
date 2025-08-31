"""
Tenant domain dependency injection providers.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_auth import TokenData
from backend.core.tenant_db import get_tenant_session
from backend.tenants.middleware import set_tenant_context_middleware


@dataclass
class AuthenticatedTenantContext:
    """
    Authenticated tenant context containing user token data and tenant database session.
    Ensures proper middleware chain execution and prevents programming errors.
    """
    token_data: TokenData
    db_session: AsyncSession

    @property
    def user_id(self) -> int | None:
        """Convenience property for user ID."""
        return self.token_data.user_id

    @property
    def tenant_subdomain(self) -> str | None:
        """Convenience property for tenant subdomain."""
        return self.token_data.tenant_subdomain

    @property
    def jti(self) -> str | None:
        """Convenience property for JWT ID."""
        return self.token_data.jti


async def get_authenticated_tenant_context(
    token_data: Annotated[TokenData, Depends(set_tenant_context_middleware)],
    db: Annotated[AsyncSession, Depends(get_tenant_session)],
) -> AuthenticatedTenantContext:
    """
    Get authenticated tenant context with user token data and tenant database session.
    This composite dependency ensures proper middleware chain execution
    and prevents programming errors from using tenant operations without context.
    """
    return AuthenticatedTenantContext(
        token_data=token_data,
        db_session=db,
    )

