"""
Session management models for user authentication tracking.
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field

from backend.core.base_models import TenantIsolatedModel, utc_now


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RevocationReason(str, Enum):
    USER_LOGOUT = "user_logout"
    USER_LOGOUT_ALL = "user_logout_all"
    ADMIN_ACTION = "admin_action"
    SECURITY_INCIDENT = "security_incident"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_SUSPENSION = "account_suspension"
    SESSION_TIMEOUT = "session_timeout"


class UserSession(TenantIsolatedModel, table=True):
    """
    Tracks active user sessions for server-side token management.
    Stored in tenant-specific schema for isolation.
    """
    __tablename__ = "user_sessions"
    __table_args__: ClassVar[dict[str, bool]] = {"extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: int = Field(index=True, foreign_key="tenant_users.id")
    token_jti: str = Field(unique=True, index=True)  # JWT ID claim for token identification

    # Device and connection information
    device_info: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ip_address: str | None = Field(nullable=True)
    user_agent: str | None = Field(nullable=True)

    # Session lifecycle
    created_at: datetime = Field(default_factory=utc_now, index=True)
    last_used_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(index=True)

    # Revocation tracking
    revoked_at: datetime | None = Field(default=None, nullable=True)
    revoked_reason: str | None = Field(default=None, nullable=True)  # String field avoids PostgreSQL enum type creation
    revoked_by: str | None = Field(default=None, nullable=True)  # User ID or "system"

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return (
            self.revoked_at is None
            and self.expires_at > utc_now()
        )

    @property
    def status(self) -> SessionStatus:
        """Get current session status."""
        if self.revoked_at is not None:
            return SessionStatus.REVOKED
        elif self.expires_at <= utc_now():
            return SessionStatus.EXPIRED
        return SessionStatus.ACTIVE

    def revoke(self, reason: RevocationReason, revoked_by: str = "system") -> None:
        """Revoke this session."""
        self.revoked_at = utc_now()
        self.revoked_reason = reason.value  # Store the string value
        self.revoked_by = revoked_by

    def touch(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = utc_now()
