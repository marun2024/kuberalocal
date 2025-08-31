"""
Auth domain read operations (Queries).
"""

from typing import Annotated

from fastapi import Depends

from backend.auth.schemas import CurrentUserResponse
from backend.core.deps import BaseContext, get_base_context


async def get_current_user_info_query(
    context: Annotated[BaseContext, Depends(get_base_context)]
) -> CurrentUserResponse:
    """Query: Get current user information from context."""
    user = context.request_user

    return CurrentUserResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_owner=user.is_owner,
        tenant_id=user.tenant.tenant_id,
        tenant_name=user.tenant.name,
        tenant_subdomain=user.tenant.subdomain,
    )
