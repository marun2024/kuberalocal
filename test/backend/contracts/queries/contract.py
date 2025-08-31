"""
Async read operations (Queries) for contracts.
"""
from __future__ import annotations
from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.core.deps import get_tenant_db
from backend.contracts.models.contract import Contract

async def get_contract_query(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Contract | None:
    res = await db.execute(select(Contract).where(Contract.id == contract_id))
    return res.scalar_one_or_none()

async def list_contracts_query(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    title_like: Optional[str] = None,
    reference_like: Optional[str] = None,
) -> list[Contract]:
    stmt = select(Contract)
    if title_like:
        stmt = stmt.where(Contract.title.ilike(f"%{title_like}%"))
    if reference_like:
        stmt = stmt.where(Contract.reference_number.ilike(f"%{reference_like}%"))
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def search_contracts_query(
    search_term: str,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> list[Contract]:
    stmt = select(Contract).where(
        or_(
            Contract.title.ilike(f"%{search_term}%"),
            Contract.reference_number.ilike(f"%{search_term}%"),
            Contract.description.ilike(f"%{search_term}%"),
            Contract.internal_owner.ilike(f"%{search_term}%"),
        )
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())