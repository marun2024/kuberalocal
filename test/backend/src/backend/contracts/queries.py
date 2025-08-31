"""
Query functions for retrieving data from the database.
Handles relationships manually without SQLAlchemy relationship mappings.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, desc

from .models import Tag, Contract, TagContractLink


# =============================================================================
# TAG QUERIES
# =============================================================================

async def get_tag_query(
    tag_id: int, 
    db: AsyncSession, 
    include_contracts: bool = False
) -> Optional[Tag]:
    """Get a single tag by ID with optional related contracts."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if tag and include_contracts:
        # Manually load related contracts via junction table
        contracts_result = await db.execute(
            select(Contract)
            .join(TagContractLink, Contract.id == TagContractLink.contract_id)
            .where(TagContractLink.tag_id == tag_id)
            .order_by(Contract.title)
        )
        contracts = contracts_result.scalars().all()
        # Add as dynamic attribute for serialization
        tag.__dict__['contracts'] = list(contracts)
    
    return tag


async def list_tags_query(
    db: AsyncSession, 
    name_like: Optional[str] = None,
    include_contracts: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Tag]:
    """List tags with optional filtering and pagination."""
    query = select(Tag)
    
    # Apply filters
    if name_like:
        query = query.where(Tag.name.ilike(f"%{name_like}%"))
    
    # Apply ordering
    query = query.order_by(Tag.name)
    
    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    if include_contracts:
        # Load contracts for each tag
        for tag in tags:
            contracts_result = await db.execute(
                select(Contract)
                .join(TagContractLink, Contract.id == TagContractLink.contract_id)
                .where(TagContractLink.tag_id == tag.id)
                .order_by(Contract.title)
            )
            contracts = contracts_result.scalars().all()
            tag.__dict__['contracts'] = list(contracts)
    
    return list(tags)


async def tag_exists_by_name(
    db: AsyncSession, 
    name: str, 
    exclude_id: Optional[int] = None
) -> bool:
    """Check if a tag with the given name already exists."""
    query = select(Tag).where(Tag.name == name)
    
    if exclude_id:
        query = query.where(Tag.id != exclude_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def count_tags_query(
    db: AsyncSession,
    name_like: Optional[str] = None
) -> int:
    """Count total number of tags matching filters."""
    query = select(func.count(Tag.id))
    
    if name_like:
        query = query.where(Tag.name.ilike(f"%{name_like}%"))
    
    result = await db.execute(query)
    return result.scalar()


# =============================================================================
# CONTRACT QUERIES
# =============================================================================

async def get_contract_query(
    contract_id: int, 
    db: AsyncSession, 
    include_tags: bool = False
) -> Optional[Contract]:
    """Get a single contract by ID with optional related tags."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if contract and include_tags:
        # Manually load related tags via junction table
        tags_result = await db.execute(
            select(Tag)
            .join(TagContractLink, Tag.id == TagContractLink.tag_id)
            .where(TagContractLink.contract_id == contract_id)
            .order_by(Tag.name)
        )
        tags = tags_result.scalars().all()
        # Add as dynamic attribute for serialization
        contract.__dict__['tags'] = list(tags)
    
    return contract


async def list_contracts_query(
    db: AsyncSession,
    title_like: Optional[str] = None,
    reference_like: Optional[str] = None,
    internal_owner_like: Optional[str] = None,
    include_tags: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Contract]:
    """List contracts with optional filtering and pagination."""
    query = select(Contract)
    
    # Apply filters
    conditions = []
    if title_like:
        conditions.append(Contract.title.ilike(f"%{title_like}%"))
    if reference_like:
        conditions.append(Contract.reference_number.ilike(f"%{reference_like}%"))
    if internal_owner_like:
        conditions.append(Contract.internal_owner.ilike(f"%{internal_owner_like}%"))
    
    if conditions:
        query = query.where(or_(*conditions))
    
    # Apply ordering
    query = query.order_by(Contract.title)
    
    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    if include_tags:
        # Load tags for each contract
        for contract in contracts:
            tags_result = await db.execute(
                select(Tag)
                .join(TagContractLink, Tag.id == TagContractLink.tag_id)
                .where(TagContractLink.contract_id == contract.id)
                .order_by(Tag.name)
            )
            tags = tags_result.scalars().all()
            contract.__dict__['tags'] = list(tags)
    
    return list(contracts)


async def search_contracts_query(
    q: str, 
    db: AsyncSession,
    include_tags: bool = False,
    limit: Optional[int] = None
) -> List[Contract]:
    """Search contracts across multiple text fields."""
    search_term = f"%{q}%"
    
    query = select(Contract).where(
        or_(
            Contract.title.ilike(search_term),
            Contract.description.ilike(search_term),
            Contract.reference_number.ilike(search_term),
            Contract.internal_owner.ilike(search_term),
            Contract.notes.ilike(search_term),
            Contract.termination_clauses.ilike(search_term),
            Contract.indemnification_terms.ilike(search_term)
        )
    ).order_by(Contract.title)
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    if include_tags:
        # Load tags for each contract
        for contract in contracts:
            tags_result = await db.execute(
                select(Tag)
                .join(TagContractLink, Tag.id == TagContractLink.tag_id)
                .where(TagContractLink.contract_id == contract.id)
                .order_by(Tag.name)
            )
            tags = tags_result.scalars().all()
            contract.__dict__['tags'] = list(tags)
    
    return list(contracts)


async def contract_exists_by_reference(
    db: AsyncSession, 
    reference_number: str, 
    exclude_id: Optional[int] = None
) -> bool:
    """Check if a contract with the given reference number already exists."""
    query = select(Contract).where(Contract.reference_number == reference_number)
    
    if exclude_id:
        query = query.where(Contract.id != exclude_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def count_contracts_query(
    db: AsyncSession,
    title_like: Optional[str] = None,
    reference_like: Optional[str] = None,
    internal_owner_like: Optional[str] = None
) -> int:
    """Count total number of contracts matching filters."""
    query = select(func.count(Contract.id))
    
    conditions = []
    if title_like:
        conditions.append(Contract.title.ilike(f"%{title_like}%"))
    if reference_like:
        conditions.append(Contract.reference_number.ilike(f"%{reference_like}%"))
    if internal_owner_like:
        conditions.append(Contract.internal_owner.ilike(f"%{internal_owner_like}%"))
    
    if conditions:
        query = query.where(or_(*conditions))
    
    result = await db.execute(query)
    return result.scalar()


# =============================================================================
# RELATIONSHIP QUERIES
# =============================================================================

async def link_exists_query(
    db: AsyncSession, 
    tag_id: int, 
    contract_id: int
) -> bool:
    """Check if a link between tag and contract already exists."""
    query = select(TagContractLink).where(
        and_(
            TagContractLink.tag_id == tag_id,
            TagContractLink.contract_id == contract_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def get_link_query(
    db: AsyncSession, 
    tag_id: int, 
    contract_id: int
) -> Optional[TagContractLink]:
    """Get a specific tag-contract link."""
    query = select(TagContractLink).where(
        and_(
            TagContractLink.tag_id == tag_id,
            TagContractLink.contract_id == contract_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_contracts_for_tag_query(
    tag_id: int, 
    db: AsyncSession
) -> List[Contract]:
    """Get all contracts linked to a specific tag."""
    result = await db.execute(
        select(Contract)
        .join(TagContractLink, Contract.id == TagContractLink.contract_id)
        .where(TagContractLink.tag_id == tag_id)
        .order_by(Contract.title)
    )
    return list(result.scalars().all())


async def get_tags_for_contract_query(
    contract_id: int, 
    db: AsyncSession
) -> List[Tag]:
    """Get all tags linked to a specific contract."""
    result = await db.execute(
        select(Tag)
        .join(TagContractLink, Tag.id == TagContractLink.tag_id)
        .where(TagContractLink.contract_id == contract_id)
        .order_by(Tag.name)
    )
    return list(result.scalars().all())


async def get_tag_with_contracts_query(
    tag_id: int, 
    db: AsyncSession
) -> Optional[Tag]:
    """Get a tag with all its linked contracts (convenience method)."""
    return await get_tag_query(tag_id, db, include_contracts=True)


async def get_contract_with_tags_query(
    contract_id: int, 
    db: AsyncSession
) -> Optional[Contract]:
    """Get a contract with all its linked tags (convenience method)."""
    return await get_contract_query(contract_id, db, include_tags=True)


async def count_links_for_tag_query(
    db: AsyncSession, 
    tag_id: int
) -> int:
    """Count how many contracts are linked to a tag."""
    result = await db.execute(
        select(func.count(TagContractLink.id)).where(TagContractLink.tag_id == tag_id)
    )
    return result.scalar()


async def count_links_for_contract_query(
    db: AsyncSession, 
    contract_id: int
) -> int:
    """Count how many tags are linked to a contract."""
    result = await db.execute(
        select(func.count(TagContractLink.id)).where(TagContractLink.contract_id == contract_id)
    )
    return result.scalar()


# =============================================================================
# ANALYTICS QUERIES
# =============================================================================

async def get_most_used_tags_query(
    db: AsyncSession, 
    limit: int = 10
) -> List[tuple[Tag, int]]:
    """Get the most frequently used tags with their usage counts."""
    result = await db.execute(
        select(Tag, func.count(TagContractLink.id).label('usage_count'))
        .join(TagContractLink, Tag.id == TagContractLink.tag_id)
        .group_by(Tag.id, Tag.name, Tag.description, Tag.created_at, Tag.last_updated_at, Tag.deleted_at, Tag.created_by, Tag.last_updated_by)
        .order_by(desc('usage_count'))
        .limit(limit)
    )
    return [(row[0], row[1]) for row in result.all()]


async def get_contracts_expiring_soon_query(
    db: AsyncSession,
    days_ahead: int = 30
) -> List[Contract]:
    """Get contracts expiring within the specified number of days."""
    from datetime import date, timedelta
    
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    result = await db.execute(
        select(Contract)
        .where(
            and_(
                Contract.end_date.is_not(None),
                Contract.end_date <= cutoff_date,
                Contract.end_date >= date.today()
            )
        )
        .order_by(Contract.end_date)
    )
    return list(result.scalars().all())


__all__ = [
    # Tag queries
    "get_tag_query", "list_tags_query", "tag_exists_by_name", "count_tags_query",
    # Contract queries  
    "get_contract_query", "list_contracts_query", "search_contracts_query", 
    "contract_exists_by_reference", "count_contracts_query",
    # Relationship queries
    "link_exists_query", "get_link_query", "get_contracts_for_tag_query", 
    "get_tags_for_contract_query", "get_tag_with_contracts_query", 
    "get_contract_with_tags_query", "count_links_for_tag_query", 
    "count_links_for_contract_query",
    # Analytics queries
    "get_most_used_tags_query", "get_contracts_expiring_soon_query"
]