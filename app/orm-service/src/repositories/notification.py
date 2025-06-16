from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Notification


class NotificationRepository:
    async def list_by_user(self, session: AsyncSession, user_id: UUID) -> Sequence[Notification]:
        stmt: Select[tuple[Notification]] = (
            select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
        )
        result: Result[tuple[Notification]] = await session.execute(stmt)
        return list(result.scalars())

    async def list_unread_by_user(self, session: AsyncSession, user_id: UUID) -> Sequence[Notification]:
        stmt: Select[tuple[Notification]] = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .order_by(Notification.created_at.desc())
        )
        result: Result[tuple[Notification]] = await session.execute(stmt)
        return list(result.scalars())

    async def mark_all_as_read(self, session: AsyncSession, user_id: UUID) -> None:
        await session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )

    async def count_unread_by_user(self, session: AsyncSession, user_id: UUID) -> int:
        stmt: Select[Tuple[int]] = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        result: Result[Tuple[int]] = await session.execute(stmt)
        return int(result.scalar_one())
