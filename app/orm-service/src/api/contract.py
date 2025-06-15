# src/api/contract.py
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contract
from src.dependencies.db import get_session_with_user
from src.repositories.tables.contract import ContractRepository
from src.utils.http_error import GoneError

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("/", response_model=None, status_code=201)
async def upload_contract(
    order_id: UUID,
    file: UploadFile = File(..., description="PDF или PNG договора"),
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await ContractRepository().add_file(session, order_id=order_id, upload=file)
    return {"detail": "Файл успешно загружен"}


@router.get("/order/{order_id}/download")
async def download_contract_by_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> FileResponse:
    repo = ContractRepository()
    contract: Contract = await repo.get_by_order(session, order_id)

    full_path: Path = Path("/app") / contract.file_path
    if not full_path.exists():
        await repo.delete(session, contract.id)
        raise GoneError("Файл договора по заказу был удалён")

    return FileResponse(path=full_path, filename=full_path.name, media_type="application/octet-stream")


@router.delete("/order/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract_by_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> None:
    repo = ContractRepository()
    await repo.delete_with_file(session, order_id)
