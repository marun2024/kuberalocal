"""
Session management commands for write operations.
"""

from datetime import datetime

from fastapi import Depends, HTTPException, Request, status

from backend.auth.jwt_auth import TokenData
from backend.sessions.models import RevocationReason, UserSession
from backend.sessions.service import SessionService
from backend.tenants.deps import (
    AuthenticatedTenantContext,
    get_authenticated_tenant_context,
)
from backend.tenants.models import TenantAuditLog

from .deps import get_session_service


async def create_session_command(
    user_id: int,
    token_jti: str,
    expires_at: datetime,
    request: Request,
    session_service: SessionService = Depends(get_session_service),
) -> UserSession:
    """Create a new user session with audit logging."""
    # Extract connection information
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Create the session
    user_session = await session_service.create_session(
        user_id=user_id,
        token_jti=token_jti,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Audit log the session creation
    db = session_service.db
    audit_log = TenantAuditLog(
        user_id=str(user_id),
        action="session_created",
        resource_type="session",
        resource_id=str(user_session.id),
        changes={
            "session_id": str(user_session.id),
            "expires_at": expires_at.isoformat(),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    await db.commit()

    return user_session


async def revoke_current_session_command(
    context: AuthenticatedTenantContext = Depends(get_authenticated_tenant_context),
    reason: RevocationReason = RevocationReason.USER_LOGOUT,
) -> dict:
    """Revoke the current user's session (logout)."""
    if not context.jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session token not found"
        )

    session_service = SessionService(context.db_session)
    revoked = await session_service.revoke_session(
        token_jti=context.jti,
        reason=reason,
        revoked_by=str(context.user_id) if context.user_id else "system"
    )

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # TODO: Add audit logging back once schema switching is stable
    return {"message": "Successfully logged out"}


async def revoke_all_sessions_command(
    token_data: TokenData,
    except_current: bool = True,
    reason: RevocationReason = RevocationReason.USER_LOGOUT_ALL,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Revoke all user sessions (logout from all devices)."""
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token"
        )

    count = await session_service.revoke_user_sessions(
        user_id=token_data.user_id,
        reason=reason,
        revoked_by=str(token_data.user_id),
        except_jti=token_data.jti if except_current else None
    )

    # Audit log the bulk logout
    db = session_service.db
    audit_log = TenantAuditLog(
        user_id=str(token_data.user_id),
        action="all_sessions_revoked",
        resource_type="session",
        changes={
            "reason": reason.value,
            "sessions_revoked": count,
            "except_current": except_current,
        },
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": f"Successfully revoked {count} session(s)",
        "sessions_revoked": count
    }


async def revoke_user_session_command(
    session_id: str,
    token_data: TokenData,
    reason: RevocationReason = RevocationReason.USER_LOGOUT,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Revoke a specific user session."""
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token"
        )

    # Get the session to verify ownership
    session = await session_service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke another user's session"
        )

    # Revoke the session
    session.revoke(reason, str(token_data.user_id))
    await session_service.db.commit()

    # Audit log
    audit_log = TenantAuditLog(
        user_id=str(token_data.user_id),
        action="session_revoked",
        resource_type="session",
        resource_id=session_id,
        changes={
            "reason": reason.value,
        },
    )
    session_service.db.add(audit_log)
    await session_service.db.commit()

    return {"message": "Session successfully revoked"}
