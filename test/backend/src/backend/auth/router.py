"""
Auth domain API routes using CQRS pattern.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.auth.commands import login_command
from backend.auth.jwt_auth import LoginRequest, Token
from backend.auth.queries import get_current_user_info_query
from backend.auth.schemas import CurrentUserResponse
from backend.sessions.commands import revoke_current_session_command

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login_endpoint(
    login_data: LoginRequest,
    token: Annotated[Token, Depends(login_command)]
) -> Token:
    """Login with email and password."""
    return token


@router.post("/logout")
async def logout_endpoint(
    result: Annotated[dict, Depends(revoke_current_session_command)]
) -> dict:
    """Logout and revoke current session."""
    return result


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info_endpoint(
    user_info: Annotated[CurrentUserResponse, Depends(get_current_user_info_query)]
) -> CurrentUserResponse:
    """Get current user information."""
    return user_info
