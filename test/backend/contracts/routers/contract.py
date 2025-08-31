from __future__ import annotations
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.deps import get_tenant_db
from backend.contracts.models.contract import Contract
from backend.contracts.schemas.contract import ContractCreate, ContractResponse, ContractUpdate
from backend.contracts.commands.contract import (
    create_contract_command,
    update_contract_command,
    delete_contract_command,
)
from backend.contracts.queries.contract import get_contract_query, list_contracts_query,search_contracts_query

router = APIRouter(prefix="/contracts", tags=["contracts"])

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract_endpoint(
    contract_data: ContractCreate,
    contract: Annotated[Contract, Depends(create_contract_command)],
) -> ContractResponse:
    return ContractResponse.model_validate(contract)

@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract_endpoint(
    contract_id: int,
    contract_data: ContractUpdate,  # <-- same name as in command
    updated: Annotated[Contract, Depends(update_contract_command)],
) -> ContractResponse:
    return ContractResponse.model_validate(updated)

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract_endpoint(
    contract_id: int,
    _: Annotated[None, Depends(delete_contract_command)],
) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract_endpoint(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> ContractResponse:
    row = await get_contract_query(contract_id, db)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return ContractResponse.model_validate(row)

@router.get("", response_model=List[ContractResponse])
async def list_contracts_endpoint(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    title_like: str | None = None,
    reference_like: str | None = None,
) -> List[ContractResponse]:
    rows = await list_contracts_query(db, title_like=title_like, reference_like=reference_like)
    return [ContractResponse.model_validate(r) for r in rows]

# ---------- SEARCH (optional async read) ----------
@router.get("/search", response_model=List[ContractResponse])
async def search_contracts_endpoint(
    q: str,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> List[ContractResponse]:
    rows = await search_contracts_query(q, db)
    return [ContractResponse.model_validate(c) for c in rows]