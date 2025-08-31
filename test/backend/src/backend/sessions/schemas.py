"""
Session management schemas for API requests and responses.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .models import RevocationReason, SessionStatus


class DeviceInfo(BaseModel):
    """Device information for session tracking."""
    platform: str | None = None
    browser: str | None = None
    version: str | None = None
    is_mobile: bool = False


class SessionCreate(BaseModel):
    """Data needed to create a new session."""
    user_id: int
    token_jti: str
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    device_info: DeviceInfo | None = None


class SessionResponse(BaseModel):
    """Session information returned to users."""
    id: UUID
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    status: SessionStatus
    device_info: dict
    ip_address: str | None
    user_agent: str | None

    class Config:
        from_attributes = True


class SessionRevoke(BaseModel):
    """Request to revoke a session."""
    session_id: UUID | None = Field(None, description="Specific session to revoke")
    reason: RevocationReason = RevocationReason.USER_LOGOUT


class BulkRevoke(BaseModel):
    """Request to revoke multiple sessions."""
    user_id: int | None = Field(None, description="Revoke all sessions for user")
    except_current: bool = Field(True, description="Keep current session active")
    reason: RevocationReason = RevocationReason.USER_LOGOUT_ALL


class SessionListResponse(BaseModel):
    """List of user sessions."""
    sessions: list[SessionResponse]
    total: int
    active_count: int
