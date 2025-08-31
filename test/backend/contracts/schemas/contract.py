# backend/contracts/schema/contract.py
from __future__ import annotations
from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel

# Fields clients are allowed to set
class ContractBase(SQLModel):
    title: Optional[str] = None
    service_provider_id: Optional[int] = None
    start_date: Optional[date] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[float] = None
    cost: Optional[float] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None

class ContractCreate(ContractBase):
    # required fields on create
    title: str
    service_provider_id: int
    start_date: date

class ContractUpdate(SQLModel):
    # all optional so PATCH can send only the fields to change
    title: Optional[str] = None
    service_provider_id: Optional[int] = None
    start_date: Optional[date] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[float] = None
    cost: Optional[float] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None

# Response schema can include audit fields (read-only)
class ContractResponse(SQLModel):
    id: int
    title: str
    service_provider_id: int
    start_date: date
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[float] = None
    cost: Optional[float] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None

    # audit (read-only)
    created_at: datetime
    last_updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_updated_by: Optional[str] = None
