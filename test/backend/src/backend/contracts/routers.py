"""
FastAPI routers for tags, contracts, and their relationships.
Complete API endpoints with pagination, filtering, and bulk operations.
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.deps import get_tenant_db
from .schemas import (
    TagCreate, TagUpdate, TagResponse,
    ContractCreate, ContractUpdate, ContractResponse,
    LinkResponse, BulkLinkRequest
)
from .queries import (
    get_tag_query, list_tags_query, count_tags_query,
    get_contract_query, list_contracts_query, search_contracts_query, count_contracts_query,
    get_contracts_for_tag_query, get_tags_for_contract_query,
    get_most_used_tags_query, get_contracts_expiring_soon_query
)
from .commands import (
    create_tag_command, update_tag_command, delete_tag_command,
    create_contract_command, update_contract_command, delete_contract_command,
    link_tag_to_contract_command, unlink_tag_from_contract_command,
    bulk_link_tags_to_contract_command, bulk_link_contracts_to_tag_command,
    bulk_unlink_tags_from_contract_command, bulk_unlink_contracts_from_tag_command,
    duplicate_tag_command, merge_tags_command, cleanup_orphaned_links_command
)


# =============================================================================
# TAG ROUTER
# =============================================================================

tag_router = APIRouter(prefix="/tags", tags=["tags"])


@tag_router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    tag_data: TagCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> TagResponse:
    """Create a new tag."""
    tag = await create_tag_command(tag_data, db)
    return TagResponse.model_validate(tag)


@tag_router.get("/{tag_id}", response_model=TagResponse)
async def get_tag_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    include_contracts: bool = Query(False, description="Include related contracts in response")
) -> TagResponse:
    """Get a tag by ID with optional related contracts."""
    tag = await get_tag_query(tag_id, db, include_contracts)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    return TagResponse.model_validate(tag)


@tag_router.get("", response_model=List[TagResponse])
async def list_tags_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    name_like: Optional[str] = Query(None, description="Filter tags by name (case insensitive partial match)"),
    include_contracts: bool = Query(False, description="Include related contracts in response"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip")
) -> List[TagResponse]:
    """List tags with optional filtering and pagination."""
    tags = await list_tags_query(db, name_like, include_contracts, limit, offset)
    return [TagResponse.model_validate(tag) for tag in tags]


@tag_router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag_endpoint(
    tag_id: int,
    tag_data: TagUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> TagResponse:
    """Update a tag (partial update)."""
    tag = await update_tag_command(tag_id, tag_data, db)
    return TagResponse.model_validate(tag)


@tag_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Response:
    """Delete a tag and all its relationships."""
    await delete_tag_command(tag_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@tag_router.post("/{tag_id}/duplicate", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_tag_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    new_name: str = Query(..., description="Name for the duplicated tag"),
) -> TagResponse:
    """Create a duplicate of an existing tag with a new name."""
    tag = await duplicate_tag_command(tag_id, new_name, db)
    return TagResponse.model_validate(tag)


@tag_router.post("/{source_tag_id}/merge/{target_tag_id}", response_model=LinkResponse)
async def merge_tags_endpoint(
    source_tag_id: int,
    target_tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> LinkResponse:
    """Merge one tag into another, transferring all relationships."""
    message = await merge_tags_command(source_tag_id, target_tag_id, db)
    return LinkResponse(message=message)


# =============================================================================
# CONTRACT ROUTER
# =============================================================================

contract_router = APIRouter(prefix="/contracts", tags=["contracts"])


@contract_router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract_endpoint(
    contract_data: ContractCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> ContractResponse:
    """Create a new contract."""
    contract = await create_contract_command(contract_data, db)
    return ContractResponse.model_validate(contract)


@contract_router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract_endpoint(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    include_tags: bool = Query(False, description="Include related tags in response")
) -> ContractResponse:
    """Get a contract by ID with optional related tags."""
    contract = await get_contract_query(contract_id, db, include_tags)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )
    return ContractResponse.model_validate(contract)


@contract_router.get("", response_model=List[ContractResponse])
async def list_contracts_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    title_like: Optional[str] = Query(None, description="Filter by title (case insensitive partial match)"),
    reference_like: Optional[str] = Query(None, description="Filter by reference number (case insensitive partial match)"),
    internal_owner_like: Optional[str] = Query(None, description="Filter by internal owner (case insensitive partial match)"),
    include_tags: bool = Query(False, description="Include related tags in response"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip")
) -> List[ContractResponse]:
    """List contracts with optional filtering and pagination."""
    contracts = await list_contracts_query(
        db, title_like, reference_like, internal_owner_like, 
        include_tags, limit, offset
    )
    return [ContractResponse.model_validate(contract) for contract in contracts]


@contract_router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract_endpoint(
    contract_id: int,
    contract_data: ContractUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> ContractResponse:
    """Update a contract (partial update)."""
    contract = await update_contract_command(contract_id, contract_data, db)
    return ContractResponse.model_validate(contract)


@contract_router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract_endpoint(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Response:
    """Delete a contract and all its relationships."""
    await delete_contract_command(contract_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@contract_router.get("/search/text", response_model=List[ContractResponse])
async def search_contracts_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    q: str = Query(..., description="Search query across contract text fields"),
    include_tags: bool = Query(False, description="Include related tags in response"),
    limit: Optional[int] = Query(50, ge=1, le=500, description="Maximum number of results")
) -> List[ContractResponse]:
    """Search contracts across multiple text fields."""
    contracts = await search_contracts_query(q, db, include_tags, limit)
    return [ContractResponse.model_validate(contract) for contract in contracts]


@contract_router.get("/expiring/soon", response_model=List[ContractResponse])
async def get_expiring_contracts_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days ahead to check for expiring contracts")
) -> List[ContractResponse]:
    """Get contracts expiring within the specified number of days."""
    contracts = await get_contracts_expiring_soon_query(db, days_ahead)
    return [ContractResponse.model_validate(contract) for contract in contracts]


# =============================================================================
# RELATIONSHIP ROUTER
# =============================================================================

relationship_router = APIRouter(prefix="/relationships", tags=["relationships"])


@relationship_router.post("/tags/{tag_id}/contracts/{contract_id}", 
                         response_model=LinkResponse, 
                         status_code=status.HTTP_201_CREATED)
async def link_tag_to_contract_endpoint(
    tag_id: int,
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Link a tag to a contract."""
    message = await link_tag_to_contract_command(tag_id, contract_id, db)
    return LinkResponse(message=message)


@relationship_router.delete("/tags/{tag_id}/contracts/{contract_id}", 
                           status_code=status.HTTP_200_OK)
async def unlink_tag_from_contract_endpoint(
    tag_id: int,
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Remove link between tag and contract."""
    message = await unlink_tag_from_contract_command(tag_id, contract_id, db)
    return LinkResponse(message=message)


@relationship_router.get("/tags/{tag_id}/contracts", response_model=List[ContractResponse])
async def get_tag_contracts_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> List[ContractResponse]:
    """Get all contracts linked to a tag."""
    # Verify tag exists first
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tag with ID {tag_id} not found"
        )
    
    contracts = await get_contracts_for_tag_query(tag_id, db)
    return [ContractResponse.model_validate(contract) for contract in contracts]


@relationship_router.get("/contracts/{contract_id}/tags", response_model=List[TagResponse])
async def get_contract_tags_endpoint(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> List[TagResponse]:
    """Get all tags linked to a contract."""
    # Verify contract exists first
    contract = await get_contract_query(contract_id, db)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Contract with ID {contract_id} not found"
        )
    
    tags = await get_tags_for_contract_query(contract_id, db)
    return [TagResponse.model_validate(tag) for tag in tags]


# =============================================================================
# BULK OPERATIONS ROUTER
# =============================================================================

bulk_router = APIRouter(prefix="/bulk", tags=["bulk-operations"])


@bulk_router.post("/contracts/{contract_id}/tags", response_model=LinkResponse)
async def bulk_link_tags_to_contract_endpoint(
    contract_id: int,
    tag_ids: List[int],
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Link multiple tags to a contract at once."""
    linked_count, errors = await bulk_link_tags_to_contract_command(contract_id, tag_ids, db)
    
    message = f"Successfully linked {linked_count} tags to contract."
    if errors:
        message += f" Errors: {'; '.join(errors)}"
    
    return LinkResponse(message=message)


@bulk_router.post("/tags/{tag_id}/contracts", response_model=LinkResponse)
async def bulk_link_contracts_to_tag_endpoint(
    tag_id: int,
    contract_ids: List[int],
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Link multiple contracts to a tag at once."""
    linked_count, errors = await bulk_link_contracts_to_tag_command(tag_id, contract_ids, db)
    
    message = f"Successfully linked {linked_count} contracts to tag."
    if errors:
        message += f" Errors: {'; '.join(errors)}"
    
    return LinkResponse(message=message)


@bulk_router.delete("/contracts/{contract_id}/tags", response_model=LinkResponse)
async def bulk_unlink_all_tags_from_contract_endpoint(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Remove all tag links from a contract."""
    unlinked_count = await bulk_unlink_tags_from_contract_command(contract_id, db)
    return LinkResponse(message=f"Successfully unlinked {unlinked_count} tags from contract")


@bulk_router.delete("/tags/{tag_id}/contracts", response_model=LinkResponse)
async def bulk_unlink_all_contracts_from_tag_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> LinkResponse:
    """Remove all contract links from a tag."""
    unlinked_count = await bulk_unlink_contracts_from_tag_command(tag_id, db)
    return LinkResponse(message=f"Successfully unlinked {unlinked_count} contracts from tag")


# =============================================================================
# ANALYTICS ROUTER
# =============================================================================

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@analytics_router.get("/tags/most-used", response_model=List[dict])
async def get_most_used_tags_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    limit: int = Query(10, ge=1, le=50, description="Number of top tags to return")
) -> List[dict]:
    """Get the most frequently used tags with their usage counts."""
    tag_usage = await get_most_used_tags_query(db, limit)
    return [
        {
            "tag": TagResponse.model_validate(tag),
            "usage_count": count
        }
        for tag, count in tag_usage
    ]


@analytics_router.get("/contracts/expiring", response_model=List[ContractResponse])
async def get_contracts_expiring_analytics_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days ahead to check")
) -> List[ContractResponse]:
    """Analytics endpoint for contracts expiring within specified days."""
    contracts = await get_contracts_expiring_soon_query(db, days_ahead)
    return [ContractResponse.model_validate(contract) for contract in contracts]


@analytics_router.get("/summary", response_model=dict)
async def get_system_summary_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> dict:
    """Get a summary of the entire contracts and tags system."""
    # Get counts
    total_tags = await count_tags_query(db)
    total_contracts = await count_contracts_query(db)
    
    # Get most used tags (top 5)
    top_tags = await get_most_used_tags_query(db, 5)
    
    # Get contracts expiring soon
    expiring_soon = await get_contracts_expiring_soon_query(db, 30)
    
    return {
        "totals": {
            "tags": total_tags,
            "contracts": total_contracts,
            "relationships": sum(count for _, count in top_tags) if top_tags else 0
        },
        "top_tags": [
            {
                "name": tag.name,
                "usage_count": count
            }
            for tag, count in top_tags
        ],
        "contracts_expiring_soon": len(expiring_soon),
        "alerts": {
            "contracts_expiring_30_days": len(expiring_soon)
        }
    }


# =============================================================================
# MAINTENANCE ROUTER
# =============================================================================

maintenance_router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@maintenance_router.post("/cleanup/orphaned-links", response_model=dict)
async def cleanup_orphaned_links_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> dict:
    """Clean up orphaned tag-contract links where referenced entities no longer exist."""
    tag_orphans, contract_orphans = await cleanup_orphaned_links_command(db)
    
    return {
        "message": "Orphaned links cleanup completed",
        "removed": {
            "orphaned_tag_links": tag_orphans,
            "orphaned_contract_links": contract_orphans,
            "total": tag_orphans + contract_orphans
        }
    }


@maintenance_router.get("/health", response_model=dict)
async def health_check_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)]
) -> dict:
    """Health check endpoint to verify system integrity."""
    try:
        # Test basic queries
        tag_count = await count_tags_query(db)
        contract_count = await count_contracts_query(db)
        
        return {
            "status": "healthy",
            "database": "connected",
            "counts": {
                "tags": tag_count,
                "contracts": contract_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


# =============================================================================
# EXPORT ALL ROUTERS
# =============================================================================

__all__ = [
    "tag_router",
    "contract_router", 
    "relationship_router",
    "bulk_router",
    "analytics_router",
    "maintenance_router"
]