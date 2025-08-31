"""
Command functions for business logic and data manipulation.
Includes full referential integrity validation for multi-tenant setup.
"""

from typing import Annotated, List, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.core.deps import get_tenant_db
from .models import Tag, Contract, TagContractLink
from .schemas import TagCreate, TagUpdate, ContractCreate, ContractUpdate
from .queries import (
    get_tag_query, tag_exists_by_name,
    get_contract_query, contract_exists_by_reference,
    link_exists_query, get_link_query
)


# =============================================================================
# TAG COMMANDS
# =============================================================================

async def create_tag_command(
    tag_data: TagCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> Tag:
    """Create a new tag with validation."""
    # Check for duplicate name
    if await tag_exists_by_name(db, tag_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{tag_data.name}' already exists"
        )
    
    # Create the tag
    tag = Tag(**tag_data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag_command(
    tag_id: int,
    tag_data: TagUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> Tag:
    """Update an existing tag with validation."""
    # Get existing tag
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check for duplicate name if name is being changed
    if tag_data.name and tag_data.name != tag.name:
        if await tag_exists_by_name(db, tag_data.name, exclude_id=tag_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag_data.name}' already exists"
            )
    
    # Update fields
    update_data = tag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag_command(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> None:
    """Delete a tag and all its relationships."""
    # Verify tag exists
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Delete all relationships first (application-level cascade delete)
    await db.execute(
        delete(TagContractLink).where(TagContractLink.tag_id == tag_id)
    )
    
    # Delete the tag
    await db.delete(tag)
    await db.commit()


# =============================================================================
# CONTRACT COMMANDS
# =============================================================================

async def create_contract_command(
    contract_data: ContractCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> Contract:
    """Create a new contract with validation."""
    # Check for duplicate reference number if provided
    if contract_data.reference_number:
        if await contract_exists_by_reference(db, contract_data.reference_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract with reference number '{contract_data.reference_number}' already exists"
            )
    
    # Create the contract
    contract = Contract(**contract_data.model_dump())
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


async def update_contract_command(
    contract_id: int,
    contract_data: ContractUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> Contract:
    """Update an existing contract with validation."""
    # Get existing contract
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )
    
    # Check for duplicate reference number if being changed
    if (contract_data.reference_number and 
        contract_data.reference_number != contract.reference_number):
        if await contract_exists_by_reference(db, contract_data.reference_number, exclude_id=contract_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract with reference number '{contract_data.reference_number}' already exists"
            )
    
    # Update fields
    update_data = contract_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    await db.commit()
    await db.refresh(contract)
    return contract


async def delete_contract_command(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> None:
    """Delete a contract and all its relationships."""
    # Verify contract exists
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )
    
    # Delete all relationships first (application-level cascade delete)
    await db.execute(
        delete(TagContractLink).where(TagContractLink.contract_id == contract_id)
    )
    
    # Delete the contract
    await db.delete(contract)
    await db.commit()


# =============================================================================
# RELATIONSHIP COMMANDS WITH REFERENTIAL INTEGRITY
# =============================================================================

async def link_tag_to_contract_command(
    tag_id: int,
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> str:
    """Link a tag to a contract with full referential integrity validation."""
    # Application-level referential integrity checks
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tag with ID {tag_id} not found"
        )
    
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Contract with ID {contract_id} not found"
        )
    
    # Check if link already exists
    if await link_exists_query(db, tag_id, contract_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Tag '{tag.name}' is already linked to contract '{contract.title}'"
        )
    
    # Create the link
    link = TagContractLink(tag_id=tag_id, contract_id=contract_id)
    db.add(link)
    await db.commit()
    
    return f"Tag '{tag.name}' successfully linked to contract '{contract.title}'"


async def unlink_tag_from_contract_command(
    tag_id: int,
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> str:
    """Remove link between tag and contract."""
    # Get the link
    link = await get_link_query(db, tag_id, contract_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No link found between tag ID {tag_id} and contract ID {contract_id}"
        )
    
    # Get tag and contract names for response message
    tag = await get_tag_query(tag_id, db)
    contract = await get_contract_query(contract_id, db)
    
    # Delete the link
    await db.delete(link)
    await db.commit()
    
    tag_name = tag.name if tag else f"ID {tag_id}"
    contract_name = contract.title if contract else f"ID {contract_id}"
    
    return f"Tag '{tag_name}' successfully unlinked from contract '{contract_name}'"


# =============================================================================
# BULK OPERATIONS WITH VALIDATION
# =============================================================================

async def bulk_link_tags_to_contract_command(
    contract_id: int,
    tag_ids: List[int],
    db: AsyncSession
) -> Tuple[int, List[str]]:
    """Bulk link multiple tags to a contract with detailed error reporting."""
    # Verify contract exists
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Contract with ID {contract_id} not found"
        )
    
    linked_count = 0
    errors = []
    
    for tag_id in tag_ids:
        try:
            # Verify tag exists
            tag = await get_tag_query(tag_id, db)
            if not tag:
                errors.append(f"Tag {tag_id}: Not found")
                continue
                
            # Check if already linked
            if await link_exists_query(db, tag_id, contract_id):
                errors.append(f"Tag {tag_id} ('{tag.name}'): Already linked to this contract")
                continue
            
            # Create link
            link = TagContractLink(tag_id=tag_id, contract_id=contract_id)
            db.add(link)
            linked_count += 1
            
        except Exception as e:
            errors.append(f"Tag {tag_id}: {str(e)}")
    
    # Commit all successful links
    if linked_count > 0:
        await db.commit()
    
    return linked_count, errors


async def bulk_link_contracts_to_tag_command(
    tag_id: int,
    contract_ids: List[int],
    db: AsyncSession
) -> Tuple[int, List[str]]:
    """Bulk link multiple contracts to a tag with detailed error reporting."""
    # Verify tag exists
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tag with ID {tag_id} not found"
        )
    
    linked_count = 0
    errors = []
    
    for contract_id in contract_ids:
        try:
            # Verify contract exists
            contract = await get_contract_query(contract_id, db)
            if not contract:
                errors.append(f"Contract {contract_id}: Not found")
                continue
                
            # Check if already linked
            if await link_exists_query(db, tag_id, contract_id):
                errors.append(f"Contract {contract_id} ('{contract.title}'): Already linked to this tag")
                continue
            
            # Create link
            link = TagContractLink(tag_id=tag_id, contract_id=contract_id)
            db.add(link)
            linked_count += 1
            
        except Exception as e:
            errors.append(f"Contract {contract_id}: {str(e)}")
    
    # Commit all successful links
    if linked_count > 0:
        await db.commit()
    
    return linked_count, errors


async def bulk_unlink_tags_from_contract_command(
    contract_id: int,
    db: AsyncSession
) -> int:
    """Remove all tag links from a contract."""
    # Verify contract exists
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Contract with ID {contract_id} not found"
        )
    
    # Get count before deletion for reporting
    result = await db.execute(
        select(TagContractLink).where(TagContractLink.contract_id == contract_id)
    )
    links = result.scalars().all()
    unlinked_count = len(links)
    
    # Delete all links for this contract
    if unlinked_count > 0:
        await db.execute(
            delete(TagContractLink).where(TagContractLink.contract_id == contract_id)
        )
        await db.commit()
    
    return unlinked_count


async def bulk_unlink_contracts_from_tag_command(
    tag_id: int,
    db: AsyncSession
) -> int:
    """Remove all contract links from a tag."""
    # Verify tag exists
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Get count before deletion for reporting
    result = await db.execute(
        select(TagContractLink).where(TagContractLink.tag_id == tag_id)
    )
    links = result.scalars().all()
    unlinked_count = len(links)
    
    # Delete all links for this tag
    if unlinked_count > 0:
        await db.execute(
            delete(TagContractLink).where(TagContractLink.tag_id == tag_id)
        )
        await db.commit()
    
    return unlinked_count


# =============================================================================
# SPECIALIZED COMMANDS
# =============================================================================

async def duplicate_tag_command(
    tag_id: int,
    new_name: str,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> Tag:
    """Create a duplicate of an existing tag with a new name."""
    # Get the original tag
    original_tag = await get_tag_query(tag_id, db)
    if not original_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check if new name already exists
    if await tag_exists_by_name(db, new_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{new_name}' already exists"
        )
    
    # Create new tag with same description but new name
    new_tag = Tag(
        name=new_name,
        description=original_tag.description
    )
    db.add(new_tag)
    await db.commit()
    await db.refresh(new_tag)
    
    return new_tag


async def merge_tags_command(
    source_tag_id: int,
    target_tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> str:
    """Merge one tag into another, transferring all relationships."""
    # Verify both tags exist
    source_tag = await get_tag_query(source_tag_id, db)
    if not source_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source tag with ID {source_tag_id} not found"
        )
    
    target_tag = await get_tag_query(target_tag_id, db)
    if not target_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target tag with ID {target_tag_id} not found"
        )
    
    if source_tag_id == target_tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge a tag with itself"
        )
    
    # Get all contracts linked to source tag
    source_links_result = await db.execute(
        select(TagContractLink).where(TagContractLink.tag_id == source_tag_id)
    )
    source_links = source_links_result.scalars().all()
    
    transferred_count = 0
    
    # Transfer relationships to target tag
    for link in source_links:
        # Check if target tag is already linked to this contract
        if not await link_exists_query(db, target_tag_id, link.contract_id):
            # Create new link for target tag
            new_link = TagContractLink(
                tag_id=target_tag_id,
                contract_id=link.contract_id
            )
            db.add(new_link)
            transferred_count += 1
        
        # Delete the source link
        await db.delete(link)
    
    # Delete the source tag
    await db.delete(source_tag)
    await db.commit()
    
    return (f"Successfully merged tag '{source_tag.name}' into '{target_tag.name}'. "
            f"Transferred {transferred_count} contract relationships.")


# =============================================================================
# UTILITY COMMANDS
# =============================================================================

async def cleanup_orphaned_links_command(
    db: AsyncSession
) -> Tuple[int, int]:
    """Clean up orphaned tag-contract links (where tag or contract no longer exists)."""
    # Find links with non-existent tags
    orphaned_tag_links = await db.execute(
        select(TagContractLink)
        .outerjoin(Tag, TagContractLink.tag_id == Tag.id)
        .where(Tag.id.is_(None))
    )
    tag_orphans = orphaned_tag_links.scalars().all()
    
    # Find links with non-existent contracts
    orphaned_contract_links = await db.execute(
        select(TagContractLink)
        .outerjoin(Contract, TagContractLink.contract_id == Contract.id)
        .where(Contract.id.is_(None))
    )
    contract_orphans = orphaned_contract_links.scalars().all()
    
    # Delete orphaned links
    total_deleted = 0
    
    for link in tag_orphans:
        await db.delete(link)
        total_deleted += 1
    
    for link in contract_orphans:
        await db.delete(link)
        total_deleted += 1
    
    if total_deleted > 0:
        await db.commit()
    
    return len(tag_orphans), len(contract_orphans)


__all__ = [
    # Tag commands
    "create_tag_command", "update_tag_command", "delete_tag_command",
    # Contract commands
    "create_contract_command", "update_contract_command", "delete_contract_command",
    # Relationship commands
    "link_tag_to_contract_command", "unlink_tag_from_contract_command",
    # Bulk operations
    "bulk_link_tags_to_contract_command", "bulk_link_contracts_to_tag_command",
    "bulk_unlink_tags_from_contract_command", "bulk_unlink_contracts_from_tag_command",
    # Specialized commands
    "duplicate_tag_command", "merge_tags_command",
    # Utility commands
    "cleanup_orphaned_links_command"
]