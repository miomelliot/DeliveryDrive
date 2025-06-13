# src/repositories/tables/base.py
from typing import Any, Protocol, Sequence, Tuple, Type
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Result, Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.http_error import ConflictError


class HasId(Protocol):
    id: Any


class CRUDRepository[
    ModelT: HasId,
    CreateT: BaseModel,
    UpdateT: BaseModel,
]:
    def __init__(self, model: Type[ModelT]) -> None:
        self.model: type[ModelT] = model

    # -------------------- READ --------------------
    async def get(self, session: AsyncSession, id: UUID) -> ModelT:
        stmt: Select[Tuple[ModelT]] = select(self.model).where(self.model.id == id)
        res: Result[Tuple[ModelT]] = await session.execute(stmt)
        instance: ModelT | None = res.scalars().first()

        if instance is None:
            raise ConflictError()

        return instance

    async def list(self, session: AsyncSession, *, offset: int = 0, limit: int = 100) -> Sequence[ModelT]:
        stmt: Select[Tuple[ModelT]] = select(self.model).offset(offset).limit(limit)
        res: Result[Tuple[ModelT]] = await session.execute(stmt)
        return res.scalars().all()

    # -------------------- CREATE --------------------
    async def create(self, session: AsyncSession, obj_in: CreateT) -> ModelT:
        db_obj: ModelT = self.model(**obj_in.model_dump())
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    # -------------------- UPDATE --------------------
    async def update(self, session: AsyncSession, db_obj: ModelT, obj_in: UpdateT) -> ModelT:
        for field, value in obj_in.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(db_obj, field, value)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update_by_id(self, session: AsyncSession, id: UUID, obj_in: UpdateT) -> ModelT:
        db_obj: ModelT = await self.get(session, id)
        return await self.update(session, db_obj, obj_in)

    # -------------------- DELETE --------------------
    async def delete(self, session: AsyncSession, id: UUID) -> None:
        await session.execute(delete(self.model).where(self.model.id == id))
