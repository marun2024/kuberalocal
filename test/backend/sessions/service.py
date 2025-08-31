"""
Session management service for creating, validating, and revoking sessions.
"""

import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.base_models import utc_now
from backend.sessions.models import RevocationReason, UserSession
from backend.sessions.schemas import DeviceInfo


class SessionService:
    """Handles all session management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_jti() -> str:
        """Generate a unique JWT ID for token identification."""
        return secrets.token_urlsafe(32)

    async def create_session(
        self,
        user_id: int,
        token_jti: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_info: DeviceInfo | None = None,
    ) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info.model_dump() if device_info else {},
        )

        self.db.add(session)
        await self.db.commit()
        return session

    async def validate_session(self, token_jti: str) -> UserSession | None:
        """
        Validate if a session is active.
        Returns the session if valid, None if invalid or not found.
        """
        # Debug: Check current search path
        import logging
        logger = logging.getLogger(__name__)

        search_path_result = await self.db.execute(text("SHOW search_path"))
        current_path = search_path_result.scalar()
        logger.debug(f"SessionService.validate_session - Current search_path: {current_path}")

        # Debug: Check if table exists in current schema
        table_check = await self.db.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions' AND table_schema = ANY(current_schemas(false)))")
        )
        table_exists = table_check.scalar()
        logger.debug(f"SessionService.validate_session - user_sessions table exists: {table_exists}")

        stmt = select(UserSession).where(UserSession.token_jti == token_jti)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session or not session.is_active:
            return None

        # Touch the session to update last_used_at
        session.touch()
        await self.db.commit()

        return session

    async def get_session(self, session_id: UUID) -> UserSession | None:
        """Get a session by ID."""
        return await self.db.get(UserSession, session_id)

    async def get_user_sessions(
        self,
        user_id: int,
        active_only: bool = False
    ) -> list[UserSession]:
        """Get all sessions for a user."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)

        if active_only:
            stmt = stmt.where(
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > utc_now()
            )

        stmt = stmt.order_by(UserSession.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def revoke_session(
        self,
        token_jti: str,
        reason: RevocationReason,
        revoked_by: str = "system"
    ) -> bool:
        """
        Revoke a specific session.
        Returns True if session was found and revoked, False otherwise.
        """
        stmt = select(UserSession).where(UserSession.token_jti == token_jti)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return False

        session.revoke(reason, revoked_by)
        await self.db.commit()

        return True

    async def revoke_user_sessions(
        self,
        user_id: int,
        reason: RevocationReason,
        revoked_by: str = "system",
        except_jti: str | None = None
    ) -> int:
        """
        Revoke all sessions for a user.
        Returns the number of sessions revoked.
        """
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None)
        )

        if except_jti:
            stmt = stmt.where(UserSession.token_jti != except_jti)

        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            session.revoke(reason, revoked_by)

        await self.db.commit()

        return len(sessions)

    async def cleanup_expired_sessions(
        self,
        older_than_days: int = 30
    ) -> int:
        """
        Remove expired sessions older than specified days.
        Returns the number of sessions deleted.
        """
        cutoff_date = utc_now() - timedelta(days=older_than_days)

        stmt = select(UserSession).where(
            UserSession.expires_at < cutoff_date
        )

        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            await self.db.delete(session)

        await self.db.commit()

        return len(sessions)

    async def get_active_session_count(self, user_id: int) -> int:
        """Get count of active sessions for a user."""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now()
        )

        result = await self.db.execute(stmt)
        return len(result.scalars().all())
