"""
Tenants domain models - includes tenant, user, audit, and invitation models.
"""

import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import ClassVar

from sqlalchemy import JSON
from sqlmodel import Column, Field

from backend.core.base_models import SharedModel, TenantIsolatedModel, utc_now


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"


class Tenant(SharedModel, table=True):
    """
    Tenant entity - stored in public schema.
    """
    __tablename__ = "tenants"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "public"}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    subdomain: str = Field(unique=True, index=True)
    schema_name: str = Field(unique=True, index=True)
    status: TenantStatus = Field(default=TenantStatus.ACTIVE, index=True)
    custom_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))


class TenantUser(TenantIsolatedModel, table=True):
    """
    Tenant-isolated user entity.
    """
    __tablename__ = "tenant_users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    password_hash: str | None = Field(default=None)  # For JWT auth
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    role: str = Field(default="member")
    is_owner: bool = Field(default=False)
    is_active: bool = Field(default=True)
    last_login: datetime | None = Field(default=None)
    custom_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))


class TenantSettings(TenantIsolatedModel, table=True):
    """
    Tenant-specific settings that tenant admins can modify.
    Stored in tenant schema, not public schema.
    """
    __tablename__ = "tenant_settings"

    id: int | None = Field(default=None, primary_key=True)
    display_name: str | None = Field(default=None)  # Override for tenant display name
    logo_url: str | None = Field(default=None)
    theme_settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
    notification_settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
    custom_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))


class TenantAuditLog(TenantIsolatedModel, table=True):
    """
    Tenant-isolated audit log for compliance and security.
    """
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    action: str = Field(index=True)
    resource_type: str = Field(nullable=True, index=True)
    resource_id: str = Field(nullable=True, index=True)
    changes: dict = Field(default_factory=dict, sa_column=Column(JSON))
    custom_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=utc_now, index=True)
    ip_address: str | None = Field(nullable=True)
    user_agent: str | None = Field(nullable=True)


class TenantInvitation(TenantIsolatedModel, table=True):
    """
    Secure invitations for tenant ownership.
    Stored in tenant-specific schema.
    """
    __tablename__ = "tenant_invitations"

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)  # Reference to tenant, no FK since it's cross-schema
    email: str = Field(index=True)
    role: str = Field(default="owner")
    token: str = Field(unique=True, index=True)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, index=True)
    expires_at: datetime = Field(index=True)
    accepted_at: datetime | None = Field(default=None)
    created_by: str = Field()  # System admin or user ID

    @classmethod
    def generate_token(cls) -> str:
        """Generate secure invitation token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_invitation(
        cls,
        tenant_id: int,
        email: str,
        role: str = "owner",
        created_by: str = "system",
        expires_hours: int = 72,
    ) -> "TenantInvitation":
        """Create new tenant invitation."""
        return cls(
            tenant_id=tenant_id,
            email=email,
            role=role,
            token=cls.generate_token(),
            expires_at=utc_now() + timedelta(hours=expires_hours),
            created_by=created_by,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    def is_expired(self) -> bool:
        """Check if invitation has expired based on expires_at timestamp."""
        return (
            self.status == InvitationStatus.PENDING
            and self.expires_at <= utc_now()
        )

    def is_valid(self) -> bool:
        """Check if invitation is still valid (pending and not expired)."""
        return (
            self.status == InvitationStatus.PENDING
            and self.expires_at > utc_now()
        )
