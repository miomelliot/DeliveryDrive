from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Notification
from src.schemas.notification import NotificationCreate


class NotificationRepository:
    async def list_by_user(self, session: AsyncSession, user_id: UUID) -> Sequence[Notification]:
        stmt: Select[tuple[Notification]] = (
            select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars())

    async def mark_as_read(self, session: AsyncSession, notification_id: UUID, user_id: UUID) -> None:
        await session.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
        )

    async def create_read(self, session: AsyncSession, data: NotificationCreate) -> Notification:
        notification = Notification(user_id=data.user_id, text=data.text, is_read=True)
        session.add(notification)
        await session.flush()
        await session.refresh(notification)
        return notification
