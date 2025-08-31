"""
Session management API endpoints.
"""


from fastapi import APIRouter, Depends

from backend.auth.deps import get_current_user
from backend.auth.jwt_auth import TokenData
from backend.sessions.schemas import SessionListResponse, SessionResponse

from .commands import (
    revoke_all_sessions_command,
    revoke_user_session_command,
)
from .queries import get_session_details_query, get_user_sessions_query

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/revoke-all")
async def revoke_all_sessions(
    except_current: bool = True,
    result: dict = Depends(revoke_all_sessions_command),
    _: TokenData = Depends(get_current_user),  # Ensure authenticated
) -> dict:
    """Revoke all sessions (logout from all devices)."""
    return result


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    active_only: bool = False,
    sessions: SessionListResponse = Depends(get_user_sessions_query),
    _: TokenData = Depends(get_current_user),  # Ensure authenticated
) -> SessionListResponse:
    """List all user sessions."""
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session: SessionResponse = Depends(get_session_details_query),
    _: TokenData = Depends(get_current_user),  # Ensure authenticated
) -> SessionResponse:
    """Get details of a specific session."""
    return session


@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    result: dict = Depends(revoke_user_session_command),
    _: TokenData = Depends(get_current_user),  # Ensure authenticated
) -> dict:
    """Revoke a specific session."""
    return result
