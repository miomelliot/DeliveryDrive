from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Notification
from src.db.session import get_session

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.patch("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(notification_id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(update(Notification).where(Notification.id == notification_id).values(is_read=True))
