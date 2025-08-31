# core/auditbase.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func

class AuditBase(SQLModel):
    # fresh Column instance + correct column name
    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=False),
            server_default=func.now(),
            nullable=False,
        )
    )

    # DO NOT reuse the created_at Column here
    last_updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "last_updated_at",
            DateTime(timezone=False),
            onupdate=func.now(),
            nullable=True,
        ),
    )

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column("deleted_at", DateTime(timezone=False), nullable=True),
    )

    created_by: Optional[str] = None
    last_updated_by: Optional[str] = None
