# src/repositories/tables/transport_type.py
from typing import Tuple

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TransportType
from src.repositories.tables.base import CRUDRepository
from src.schemas.transport_type import TransportTypeCreate, TransportTypeUpdate
from src.utils.http_error import ConflictError


class TransportTypeRepository(CRUDRepository[TransportType, TransportTypeCreate, TransportTypeUpdate]):
    def __init__(self) -> None:
        super().__init__(TransportType)

    async def get_id(self, session: AsyncSession, name: str) -> int:
        stmt: Select[Tuple[int]] = select(self.model.id).where(self.model.name == name)
        res: Result[Tuple[int]] = await session.execute(stmt)
        instance: int | None = res.scalars().first()

        if instance is None:
            raise ConflictError("Объект с таким ID не найден")

        return instance
