from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Get current UTC time without timezone info for PostgreSQL TIMESTAMP."""
    # PostgreSQL TIMESTAMP WITHOUT TIME ZONE expects naive datetime
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampedBase(SQLModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SharedModel(TimestampedBase):
    """Base class for models in public schema shared across tenants."""

    __table_args__ = {"schema": "public"}


class TenantIsolatedModel(TimestampedBase):
    """Base class for models isolated per tenant schema."""

    pass
