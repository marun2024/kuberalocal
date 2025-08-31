"""
Session management queries for read operations.
"""

from fastapi import Depends, HTTPException, status

from backend.auth.jwt_auth import TokenData
from backend.sessions.schemas import SessionListResponse, SessionResponse
from backend.sessions.service import SessionService

from .deps import get_session_service


async def get_user_sessions_query(
    token_data: TokenData,
    active_only: bool = False,
    session_service: SessionService = Depends(get_session_service),
) -> SessionListResponse:
    """Get all sessions for the current user."""
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token"
        )

    sessions = await session_service.get_user_sessions(
        user_id=token_data.user_id,
        active_only=active_only
    )

    # Convert to response models
    session_responses = [
        SessionResponse.model_validate(session)
        for session in sessions
    ]

    # Count active sessions
    active_count = sum(1 for s in sessions if s.is_active)

    return SessionListResponse(
        sessions=session_responses,
        total=len(sessions),
        active_count=active_count
    )


async def validate_session_query(
    token_jti: str,
    session_service: SessionService = Depends(get_session_service),
) -> bool:
    """
    Check if a session is valid.
    Used internally by middleware for token validation.
    """
    session = await session_service.validate_session(token_jti)
    return session is not None


async def get_session_details_query(
    session_id: str,
    token_data: TokenData,
    session_service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Get details of a specific session."""
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token"
        )

    session = await session_service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify the session belongs to the requesting user
    if session.user_id != token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's session"
        )

    return SessionResponse.model_validate(session)
