# src/repositories/tables/base_status.py
from typing import Tuple

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import BaseLookup
from src.repositories.tables.base import CRUDRepository
from src.schemas.base_lookup import BaseLookupCreate, BaseLookupUpdate
from src.utils.http_error import ConflictError


class BaseStatusRepository(CRUDRepository[BaseLookup, BaseLookupCreate, BaseLookupUpdate]):
    def __init__(self) -> None:
        super().__init__(BaseLookup)

    async def get_id(self, session: AsyncSession, code: str) -> int:
        stmt: Select[Tuple[int]] = select(self.model.id).where(self.model.code == code)
        res: Result[Tuple[int]] = await session.execute(stmt)
        instance: int | None = res.scalars().first()

        if instance is None:
            raise ConflictError("Объект с таким ID не найден")

        return instance

