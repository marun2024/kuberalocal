from __future__ import annotations

from typing import Annotated
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from datetime import datetime
from backend.core.deps import get_tenant_db
from backend.core.base_models import utc_now
from backend.contracts.models.contract import Contract
from backend.contracts.schemas.contract import ContractCreate, ContractUpdate

# ---------- CREATE ----------
async def create_contract_command(
    contract_data: ContractCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Contract:
    # Optional: enforce unique reference_number if provided
    if contract_data.reference_number:
        dup = (
            await db.execute(
                select(Contract).where(Contract.reference_number == contract_data.reference_number)
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contract with this reference number already exists.",
            )

    contract = Contract(**contract_data.model_dump(exclude_unset=True))

    try:
        db.add(contract)
        # INSERT now; PK assigned
        await db.flush()
        # No refresh needed (expire_on_commit=False)
        await db.commit()
        return contract

    except IntegrityError as ie:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error creating contract: {ie.orig}",
        ) from ie
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create contract: {e}",
        ) from e


# ---------- UPDATE (PATCH) ----------
async def update_contract_command(
    contract_id: int,
    contract_data: ContractUpdate,  # <-- body name
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> Contract:
    res = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # optional uniqueness check for reference_number
    if contract_data.reference_number and contract_data.reference_number != contract.reference_number:
        dup = (await db.execute(
            select(Contract).where(
                Contract.reference_number == contract_data.reference_number,
                Contract.id != contract_id
            )
        )).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=409, detail="Reference number already exists")

    # apply partial updates
    for k, v in contract_data.model_dump(exclude_unset=True).items():
        setattr(contract, k, v)

    if hasattr(contract, "last_updated_at"):
        contract.last_updated_at = datetime.utcnow()

    try:
        await db.flush()
        await db.commit()   # with expire_on_commit=False, no refresh needed
        return contract
    except IntegrityError as ie:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error updating contract: {ie.orig}") from ie
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update contract: {e}") from e

# ---------- DELETE ----------
async def delete_contract_command(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> None:
    res = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    try:
        # Hard delete
        await db.delete(contract)
        await db.commit()

        # If you prefer soft delete, do this instead:
        # contract.deleted_at = datetime.utcnow()
        # await db.flush()
        # await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete contract: {e}",
        ) from e