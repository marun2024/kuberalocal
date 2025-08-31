from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.core.deps import get_tenant_db
from backend.contracts.models.tag import Tag
from backend.contracts.schemas.tag import TagCreate, TagUpdate


# -----------------------------
# CREATE
# -----------------------------
async def create_tag_command(
    tag_data: TagCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Tag:
    # Optional pre-check for clearer 409s
    existing = (await db.execute(select(Tag).where(Tag.name == tag_data.name))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )

    tag = Tag(**tag_data.model_dump())

    try:
        db.add(tag)
        await db.flush()          # ensure INSERT, PK assigned
        await db.refresh(tag)     # load fields (if needed)
        await db.commit()
        return tag

    except IntegrityError as ie:
        await db.rollback()
        # Unique constraint race protection
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        ) from ie
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tag: {e}",
        ) from e


# -----------------------------
# UPDATE (PATCH)
# -----------------------------
async def update_tag_command(
    tag_id: int,
    tag_data: TagUpdate,   # name matches endpoint body
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Tag:
    res = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # optional unique name check
    if tag_data.name is not None and tag_data.name != tag.name:
        dup = (await db.execute(select(Tag).where(Tag.name == tag_data.name))).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag with this name already exists")

    # apply partial updates
    for k, v in tag_data.model_dump(exclude_unset=True).items():
        setattr(tag, k, v)

    # audit
    if hasattr(tag, "last_updated_at"):
        tag.last_updated_at = datetime.utcnow()

    await db.flush()   # issue UPDATE
    await db.commit()  # instance remains valid thanks to expire_on_commit=False
    return tag         # no refresh/re-query needed

# -----------------------------
# DELETE
# -----------------------------
async def delete_tag_command(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    try:
        # Hard delete:
        await db.delete(tag)
        await db.commit()

        # If you prefer soft delete:
        # tag.deleted_at = datetime.utcnow()
        # await db.flush()
        # await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete tag: {e}",
        ) from e
