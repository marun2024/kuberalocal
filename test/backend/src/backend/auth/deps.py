"""
Auth domain dependency injection providers.
"""

from typing import Annotated

from fastapi import Depends

from backend.auth.jwt_auth import TokenData
from backend.sessions.middleware import validate_session


async def get_current_user(
    token_data: Annotated[TokenData, Depends(validate_session)]
) -> TokenData:
    """
    Get current authenticated user with session validation.
    This replaces direct use of verify_token for protected endpoints.
    """
    return token_data
