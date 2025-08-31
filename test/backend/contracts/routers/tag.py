from __future__ import annotations

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.deps import get_tenant_db
from backend.contracts.models.tag import Tag
from backend.contracts.schemas.tag import TagCreate, TagUpdate, TagResponse
from backend.contracts.commands.tag import (
    create_tag_command,
    update_tag_command,
    delete_tag_command,
)
from backend.contracts.queries.tag import get_tag_query, list_tags_query

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    tag_data: TagCreate,
    tag: Annotated[Tag, Depends(create_tag_command)],
) -> TagResponse:
    """Create a new tag."""
    return TagResponse.model_validate(tag)

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag_endpoint(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> TagResponse:
    """Fetch a tag by id."""
    tag = await get_tag_query(tag_id, db)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return TagResponse.model_validate(tag)

@router.get("", response_model=List[TagResponse])
async def list_tags_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    name_like: str | None = None,
) -> List[TagResponse]:
    """List tags (optionally filter by name substring)."""
    rows = await list_tags_query(db, name_like=name_like)
    return [TagResponse.model_validate(t) for t in rows]

@router.patch("/{tag_id}", response_model=TagResponse, summary="Update tag (partial)")
async def update_tag_endpoint(
    tag_id: int,
    tag_data: TagUpdate,
    tag: Annotated[Tag, Depends(update_tag_command)],
) -> TagResponse:
    """Update a tag via command layer."""
    return TagResponse.model_validate(tag)

@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    response_class=Response,
)
async def delete_tag_endpoint(
    tag_id: int,
    _: Annotated[None, Depends(delete_tag_command)],
) -> Response:
    """Delete a tag via command layer."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
