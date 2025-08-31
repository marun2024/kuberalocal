from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import UniqueConstraint
from backend.core.auditbase import AuditBase
from datetime import datetime
from sqlalchemy.types import String, Text, Date, Boolean, Numeric, Integer, Interval
from sqlalchemy import DateTime, func
from .contract import TagContract

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

class Tag(AuditBase, table=True):
    __tablename__ = "tag"
    __table_args__ = (UniqueConstraint("name", name="uq_tag_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)  
    description: Optional[str] = None
    contract_tag: List["TagContract"] = Relationship(back_populates="tag")

    
