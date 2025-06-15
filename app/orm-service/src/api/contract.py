# src/api/contract.py
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contract
from src.dependencies.db import get_session_with_user
from src.repositories.tables.contract import ContractRepository
from src.schemas.contract import ContractRead

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("/", response_model=ContractRead, status_code=201)
async def upload_contract(
    order_id: UUID,
    file: UploadFile = File(..., description="PDF или PNG договора"),
    session: AsyncSession = Depends(get_session_with_user),
) -> Contract:
    return await ContractRepository().add_file(session, order_id=order_id, upload=file)
