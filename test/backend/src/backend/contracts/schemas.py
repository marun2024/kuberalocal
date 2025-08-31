"""
Pydantic schemas for contracts and tags API.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from sqlmodel import SQLModel


# =============================================================================
# TAG SCHEMAS
# =============================================================================

class TagBase(SQLModel):
    """Base schema for tag with common fields."""
    name: str
    description: Optional[str] = None


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class TagUpdate(SQLModel):
    """Schema for updating a tag (all fields optional for PATCH)."""
    name: Optional[str] = None
    description: Optional[str] = None


class TagResponse(SQLModel):
    """Schema for tag responses including audit fields."""
    id: int
    name: str
    description: Optional[str] = None
    
    # Audit fields (read-only)
    created_at: datetime
    last_updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_updated_by: Optional[str] = None
    
    # Optional related data (populated when include_contracts=True)
    contracts: Optional[List["ContractResponse"]] = None


class TagRead(SQLModel):
    """Schema for reading tags (alias for response)."""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# CONTRACT SCHEMAS
# =============================================================================

class ContractBase(SQLModel):
    """Base schema for contract with common fields."""
    title: Optional[str] = None
    service_provider_id: Optional[int] = None
    start_date: Optional[date] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    """Schema for creating a new contract (required fields specified)."""
    title: str  # Required
    service_provider_id: int  # Required
    start_date: date  # Required


class ContractUpdate(SQLModel):
    """Schema for updating a contract (all fields optional for PATCH)."""
    title: Optional[str] = None
    service_provider_id: Optional[int] = None
    start_date: Optional[date] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None


class ContractResponse(SQLModel):
    """Schema for contract responses including all fields and audit data."""
    id: int
    title: str
    service_provider_id: int
    start_date: date
    reference_number: Optional[str] = None
    description: Optional[str] = None
    end_date: Optional[date] = None
    auto_renewal_date: Optional[date] = None
    signature_date: Optional[date] = None
    total_value: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    payment_schedule_type_id: Optional[int] = None
    internal_owner: Optional[str] = None
    license_count: Optional[int] = None
    termination_clauses: Optional[str] = None
    indemnification_terms: Optional[str] = None
    renewal_alert_flag: Optional[bool] = None
    notes: Optional[str] = None

    # Audit fields (read-only)
    created_at: datetime
    last_updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_updated_by: Optional[str] = None
    
    # Optional related data (populated when include_tags=True)
    tags: Optional[List["TagResponse"]] = None


class ContractRead(SQLModel):
    """Schema for reading contracts (alias for response)."""
    id: int
    title: str
    service_provider_id: int
    start_date: date
    
    class Config:
        from_attributes = True


# =============================================================================
# RELATIONSHIP SCHEMAS
# =============================================================================

class LinkRequest(SQLModel):
    """Schema for linking tags and contracts."""
    tag_id: int
    contract_id: int


class LinkResponse(SQLModel):
    """Schema for link operation responses."""
    message: str


class BulkLinkRequest(SQLModel):
    """Schema for bulk linking operations."""
    ids: List[int]


# =============================================================================
# SEARCH AND FILTER SCHEMAS
# =============================================================================

class TagFilter(SQLModel):
    """Schema for tag filtering parameters."""
    name_like: Optional[str] = None
    include_contracts: Optional[bool] = False


class ContractFilter(SQLModel):
    """Schema for contract filtering parameters."""
    title_like: Optional[str] = None
    reference_like: Optional[str] = None
    internal_owner_like: Optional[str] = None
    include_tags: Optional[bool] = False


class ContractSearch(SQLModel):
    """Schema for contract search parameters."""
    q: str
    include_tags: Optional[bool] = False


# Resolve forward references for circular dependencies
TagResponse.model_rebuild()
ContractResponse.model_rebuild()


__all__ = [
    # Tag schemas
    "TagBase", "TagCreate", "TagUpdate", "TagResponse", "TagRead",
    # Contract schemas  
    "ContractBase", "ContractCreate", "ContractUpdate", "ContractResponse", "ContractRead",
    # Relationship schemas
    "LinkRequest", "LinkResponse", "BulkLinkRequest",
    # Filter schemas
    "TagFilter", "ContractFilter", "ContractSearch"
]