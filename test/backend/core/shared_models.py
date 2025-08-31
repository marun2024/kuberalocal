from typing import ClassVar

from sqlalchemy import JSON
from sqlmodel import Column, Field

from backend.core.base_models import SharedModel


class SystemConfiguration(SharedModel, table=True):
    """
    System-wide configuration that applies to all tenants.
    Lives in public schema.
    """

    __tablename__ = "system_configurations"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "public"}

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: dict = Field(default_factory=dict, sa_column=Column(JSON))
    description: str | None = Field(default=None)
    is_sensitive: bool = Field(default=False)  # For hiding in logs/UI
