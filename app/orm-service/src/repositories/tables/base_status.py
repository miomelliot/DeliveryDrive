from typing import Any, Protocol, Tuple

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.tables.base import CRUDRepository
from src.schemas.base_lookup import BaseLookupCreate, BaseLookupUpdate
from src.utils.http_error import ConflictError


class HasIdAndCode(Protocol):
    id: Any
    code: Any


class BaseStatusRepository[ModelT: HasIdAndCode](CRUDRepository[ModelT, BaseLookupCreate, BaseLookupUpdate]):
    def __init__(self, model: type[ModelT]) -> None:
        super().__init__(model)

    async def get_id(self, session: AsyncSession, code: str) -> int:
        stmt: Select[Tuple[int]] = select(self.model.id).where(self.model.code == code)
        res: Result[Tuple[int]] = await session.execute(stmt)
        instance: int | None = res.scalars().first()

        if instance is None:
            raise ConflictError("Объект с таким кодом не найден")

        return instance
