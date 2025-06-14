# src/repositories/tables/heater_type.py
from typing import Tuple

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import HeaterType
from src.repositories.tables.base import CRUDRepository
from src.schemas.heater_type import HeaterTypeCreate, HeaterTypeUpdate
from src.utils.http_error import NotFoundError


class HeaterTypeRepository(CRUDRepository[HeaterType, HeaterTypeCreate, HeaterTypeUpdate]):
    def __init__(self) -> None:
        super().__init__(HeaterType)

    async def get_id(self, session: AsyncSession, model: str) -> int:
        stmt: Select[Tuple[int]] = select(self.model.id).where(self.model.model == model)
        res: Result[Tuple[int]] = await session.execute(stmt)
        instance: int | None = res.scalars().first()

        if instance is None:
            raise NotFoundError(f"{model} не найдено")

        return instance
