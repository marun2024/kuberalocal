"""
Asynchronous domain read operations (Queries) for all models.
Pattern: AsyncSession + Depends(get_async_session) + SQLModel select.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Optional, List

from fastapi import Depends
from sqlalchemy import or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

#from app.core.db_async import get_async_session
from backend.core.deps import get_tenant_db

from backend.contracts.models.tag import Tag
# =====================================================
# Tag
# =====================================================
async def get_tag_query(tag_id: int, db: Annotated[AsyncSession, Depends(get_tenant_db)]) -> Tag | None:
    stmt = select(Tag).where(Tag.id == tag_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_tags_query(db: Annotated[AsyncSession, Depends(get_tenant_db)], name_like: str | None = None) -> list[Tag]:
    stmt = select(Tag)
    if name_like:
        stmt = stmt.where(Tag.name.ilike(f"%{name_like}%"))
    res = await db.execute(stmt)
    return list(res.scalars().all())