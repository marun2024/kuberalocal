from __future__ import annotations

from typing import Optional,List
from datetime import date, timedelta
from decimal import Decimal
from datetime import datetime
from sqlmodel import SQLModel, Field, Column,Relationship
from sqlalchemy import UniqueConstraint
from sqlalchemy.types import String, Text, Date, Boolean, Numeric, Integer, Interval
from sqlalchemy import DateTime, func
from .tag import Tag

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


class Contract(AuditBase, table=True):
    __tablename__ = "contract"
    __table_args__ = (
        UniqueConstraint("reference_number", name="uq_contract_reference_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # core fields
    title: str = Field(sa_column=Column(String(255), nullable=False))
    service_provider_id: int = Field(sa_column=Column(Integer, nullable=False))
    reference_number: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))

    # dates and intervals
    start_date: date = Field(sa_column=Column(Date, nullable=False))
    end_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    auto_renewal_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    renewal_notice_deadline: Optional[timedelta] = Field(default=None, sa_column=Column(Interval))
    signature_date: Optional[date] = Field(default=None, sa_column=Column(Date))

    # money / misc
    total_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 2)))
    cost: Optional[Decimal] = Field(default=None, sa_column=Column("cost", Numeric(18, 2)))
    payment_schedule_type_id: Optional[int] = Field(default=None, sa_column=Column(Integer))
    internal_owner: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    license_count: Optional[int] = Field(default=None, sa_column=Column(Integer))
    termination_clauses: Optional[str] = Field(default=None, sa_column=Column(Text))
    indemnification_terms: Optional[str] = Field(default=None, sa_column=Column(Text))
    renewal_alert_flag: bool = Field(default=False, sa_column=Column(Boolean, server_default="false"))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    tag_contract: List["TagContract"] = Relationship(back_populates="contract")


class TagContract(AuditBase, table=True):
    tag_id: int = Field(foreign_key="tag.id")
    contract_id: int = Field(foreign_key="contract.id")
    __tablename__ = "tag_contract"
    id: Optional[int] = Field(default=None, primary_key=True)
    Contract: List["Contract"] = Relationship(back_populates="tag_contract")
    Tag: List["Tag"] = Relationship(back_populates="tag_contract")