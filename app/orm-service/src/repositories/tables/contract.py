# src/repositories/tables/contract.py
import secrets
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contract
from src.repositories.tables.base import CRUDRepository
from src.schemas.contract import ContractCreate, ContractUpdate
from src.utils.http_error import BadRequestError

CONTRACT_DIR = Path("/app/static/contracts")
ALLOWED: set[str] = {".pdf", ".png"}


class ContractRepository(CRUDRepository[Contract, ContractCreate, ContractUpdate]):
    def __init__(self) -> None:
        super().__init__(Contract)

    async def add_file(
        self,
        session: AsyncSession,
        *,
        order_id: UUID,
        upload: UploadFile,
    ) -> Contract:
        if not upload.filename:
            raise BadRequestError("Отсутствует имя файла")
        ext: str = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED:
            raise BadRequestError("Недопустимый формат фала принимаеться только .pdf или .png")

        CONTRACT_DIR.mkdir(parents=True, exist_ok=True)

        filename: str = f"{secrets.token_hex(16)}{ext}"
        dest: Path = CONTRACT_DIR / filename

        async with aiofiles.open(dest, "wb") as f:
            while chunk := await upload.read(8192):
                await f.write(chunk)

        rel_path: Path = dest.relative_to("/app")

        obj_in = ContractCreate(order_id=order_id, file_path=str(rel_path))
        return await super().create(session, obj_in)
