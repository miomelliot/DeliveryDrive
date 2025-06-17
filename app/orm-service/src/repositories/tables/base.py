# src/repositories/tables/base.py
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Protocol, Sequence, Tuple
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Result, Select, delete, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AuditLog
from src.utils.http_error import NotFoundError


class HasId(Protocol):
    id: Any


class CRUDRepository[
    ModelT: HasId,
    CreateT: BaseModel,
    UpdateT: BaseModel,
]:
    def __init__(self, model: type[ModelT]) -> None:
        self.model: type[ModelT] = model

    #  helpers 
    @staticmethod
    def _to_serializable(value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _as_dict(instance: Any) -> dict[str, Any]:
        mapper = inspect(instance)
        return {c.key: CRUDRepository._to_serializable(getattr(instance, c.key)) for c in mapper.mapper.column_attrs}

    async def _write_log(
        self,
        session: AsyncSession,
        *,
        event: str,
        old_values: dict[str, Any] | None,
        new_values: dict[str, Any] | None,
    ) -> None:
        session.add(
            AuditLog(
                user_id=session.info.get("user_id"),
                event=event,
                target_table=self.model.__tablename__,  # type: ignore
                old_values=old_values,
                new_values=new_values,
            )
        )

    # -- READ --
    async def get(self, session: AsyncSession, id: UUID | int) -> ModelT:
        stmt: Select[Tuple[ModelT]] = select(self.model).where(self.model.id == id)
        res: Result[Tuple[ModelT]] = await session.execute(stmt)
        instance: ModelT | None = res.scalars().first()

        if instance is None:
            raise NotFoundError()

        return instance

    async def list(self, session: AsyncSession, *, offset: int = 0, limit: int = 100) -> Sequence[ModelT]:
        stmt: Select[Tuple[ModelT]] = select(self.model).offset(offset).limit(limit)
        res: Result[Tuple[ModelT]] = await session.execute(stmt)
        return res.scalars().all()

    # -- CREATE --
    async def create(self, session: AsyncSession, obj_in: CreateT) -> ModelT:
        db_obj: ModelT = self.model(**obj_in.model_dump())
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)

        await self._write_log(
            session,
            event="CREATE",
            old_values=None,
            new_values=self._as_dict(db_obj),
        )
        return db_obj

    # -- UPDATE --
    async def update(self, session: AsyncSession, db_obj: ModelT, obj_in: UpdateT) -> ModelT:
        old_snapshot: dict[str, Any] = self._as_dict(db_obj)

        for field, value in obj_in.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(db_obj, field, value)

        await session.flush()
        await session.refresh(db_obj)

        await self._write_log(
            session,
            event="UPDATE",
            old_values=old_snapshot,
            new_values=self._as_dict(db_obj),
        )
        return db_obj

    async def update_by_id(self, session: AsyncSession, id: UUID | int, obj_in: UpdateT) -> ModelT:
        db_obj: ModelT = await self.get(session, id)
        return await self.update(session, db_obj, obj_in)

    # -- DELETE --
    async def delete(self, session: AsyncSession, id: UUID | int) -> None:
        instance: ModelT = await self.get(session, id)
        await session.execute(delete(self.model).where(self.model.id == id))

        await self._write_log(
            session,
            event="DELETE",
            old_values=self._as_dict(instance),
            new_values=None,
        )
