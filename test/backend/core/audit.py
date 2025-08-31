from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.core.base_models import utc_now
from backend.tenants.models import TenantAuditLog


class AuditService:
    """
    Service for managing tenant-isolated audit logs.
    All audit logs are stored in the tenant's schema for regulatory compliance.
    """

    @staticmethod
    async def log_action(
        session: AsyncSession,
        user_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TenantAuditLog:
        """
        Log an action in the current tenant context.
        This will be stored in the tenant's isolated schema.
        """
        audit_log = TenantAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=utc_now(),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        session.add(audit_log)

        return audit_log

    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TenantAuditLog]:
        """
        Retrieve audit logs for the current tenant.
        All filtering happens within the tenant's isolated schema.
        """
        statement = select(TenantAuditLog)

        if user_id:
            statement = statement.where(TenantAuditLog.user_id == user_id)

        if action:
            statement = statement.where(TenantAuditLog.action == action)

        if resource_type:
            statement = statement.where(TenantAuditLog.resource_type == resource_type)

        if resource_id:
            statement = statement.where(TenantAuditLog.resource_id == resource_id)

        if start_date:
            statement = statement.where(TenantAuditLog.timestamp >= start_date)

        if end_date:
            statement = statement.where(TenantAuditLog.timestamp <= end_date)

        statement = (
            statement.order_by(TenantAuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_audit_log(
        session: AsyncSession, audit_log_id: int
    ) -> TenantAuditLog | None:
        """Get a specific audit log by ID within tenant context."""
        statement = select(TenantAuditLog).where(TenantAuditLog.id == audit_log_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_activity(
        session: AsyncSession, user_id: int, days: int = 30
    ) -> list[TenantAuditLog]:
        """Get recent activity for a specific user within the tenant."""
        from datetime import timedelta

        start_date = utc_now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days)

        statement = (
            select(TenantAuditLog)
            .where(TenantAuditLog.user_id == user_id)
            .where(TenantAuditLog.timestamp >= start_date)
            .order_by(TenantAuditLog.timestamp.desc())
            .limit(100)
        )

        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_resource_history(
        session: AsyncSession, resource_type: str, resource_id: str
    ) -> list[TenantAuditLog]:
        """Get all audit logs for a specific resource within the tenant."""
        statement = (
            select(TenantAuditLog)
            .where(TenantAuditLog.resource_type == resource_type)
            .where(TenantAuditLog.resource_id == resource_id)
            .order_by(TenantAuditLog.timestamp.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def count_audit_logs(
        session: AsyncSession,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count audit logs matching the criteria within tenant context."""
        from sqlalchemy import func

        statement = select(func.count(TenantAuditLog.id))

        if user_id:
            statement = statement.where(TenantAuditLog.user_id == user_id)

        if action:
            statement = statement.where(TenantAuditLog.action == action)

        if resource_type:
            statement = statement.where(TenantAuditLog.resource_type == resource_type)

        if start_date:
            statement = statement.where(TenantAuditLog.timestamp >= start_date)

        if end_date:
            statement = statement.where(TenantAuditLog.timestamp <= end_date)

        result = await session.execute(statement)
        return result.scalar() or 0


# Helper function for easy audit logging
async def log_audit(
    session: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    changes: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TenantAuditLog:
    """Convenience function for logging audit events."""
    return await AuditService.log_action(
        session=session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
