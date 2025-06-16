# src/repositories/tables/contract.py
import secrets
from pathlib import Path
from typing import Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contract
from src.repositories.tables.base import CRUDRepository
from src.schemas.contract import ContractCreate, ContractUpdate
from src.utils.http_error import BadRequestError, NotFoundError

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
            raise BadRequestError("Недопустимый формат файла. Принимаются только .pdf или .png")

        try:
            existing: Contract = await self.get_by_order(session, order_id)
            old_path: Path = Path("/app") / existing.file_path
            if old_path.exists():
                old_path.unlink(missing_ok=True)
            await super().delete(session, existing.id)
        except NotFoundError:
            pass

        CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
        filename: str = f"{secrets.token_hex(16)}{ext}"
        dest: Path = CONTRACT_DIR / filename

        async with aiofiles.open(dest, "wb") as f:
            while chunk := await upload.read(8192):
                await f.write(chunk)

        rel_path: Path = dest.relative_to("/app")
        obj_in = ContractCreate(order_id=order_id, file_path=str(rel_path))
        return await super().create(session, obj_in)

    async def get_by_order(self, session: AsyncSession, order_id: UUID) -> Contract:
        stmt: Select[Tuple[Contract]] = select(self.model).where(self.model.order_id == order_id)
        result: Result[Tuple[Contract]] = await session.execute(stmt)
        instance: Contract | None = result.scalars().first()
        if not instance:
            raise NotFoundError("Контракт по заказу не найден")
        return instance

    async def delete_with_file(self, session: AsyncSession, order_id: UUID) -> None:
        contract: Contract = await self.get_by_order(session, order_id)
        file_path: Path = Path("/app") / contract.file_path
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        await super().delete(session, contract.id)
