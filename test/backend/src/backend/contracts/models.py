"""
Models for contracts and tags with many-to-many relationships.
"""

from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
from decimal import Decimal

from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from sqlalchemy.types import Text, Date, Boolean, Numeric, Interval

from backend.core.core_common_base import CoreCommonBase


class TagContractLink(CoreCommonBase, table=True):
    """Many-to-many link table between tags and contracts."""
    __tablename__ = "tag_contract_link"
    __table_args__ = (
        UniqueConstraint("tag_id", "contract_id", name="uq_tag_contract"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tag.id")
    contract_id: int = Field(foreign_key="contract.id")


class Tag(CoreCommonBase, table=True):
    """Tag model for categorizing contracts."""
    __tablename__ = "tag"
    __table_args__ = (
        UniqueConstraint("name", name="uq_tag_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, sa_type=Text)


class Contract(CoreCommonBase, table=True):
    """Contract model for managing service agreements."""
    __tablename__ = "contract"
    __table_args__ = (
        UniqueConstraint("reference_number", name="uq_contract_reference_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Core fields
    title: str = Field(max_length=255)
    service_provider_id: int = Field()
    reference_number: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, sa_type=Text)

    # Dates and intervals
    start_date: date = Field(sa_type=Date)
    end_date: Optional[date] = Field(default=None, sa_type=Date)
    auto_renewal_date: Optional[date] = Field(default=None, sa_type=Date)
    renewal_notice_deadline: Optional[timedelta] = Field(default=None, sa_type=Interval)
    signature_date: Optional[date] = Field(default=None, sa_type=Date)

    # Money / misc
    total_value: Optional[Decimal] = Field(default=None, sa_type=Numeric(18, 2))
    cost: Optional[Decimal] = Field(default=None, sa_type=Numeric(18, 2))
    payment_schedule_type_id: Optional[int] = Field(default=None)
    internal_owner: Optional[str] = Field(default=None, max_length=255)
    license_count: Optional[int] = Field(default=None)
    termination_clauses: Optional[str] = Field(default=None, sa_type=Text)
    indemnification_terms: Optional[str] = Field(default=None, sa_type=Text)
    renewal_alert_flag: bool = Field(default=False, sa_type=Boolean)
    notes: Optional[str] = Field(default=None, sa_type=Text)


__all__ = ["Tag", "Contract", "TagContractLink"]