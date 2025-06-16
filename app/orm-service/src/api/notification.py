from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Notification
from src.dependencies.auth import get_current_user
from src.dependencies.db import get_session_with_user
from src.repositories.notification import NotificationRepository
from src.schemas.auth import CurrentUser
from src.schemas.notification import NotificationCreate, NotificationRead

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationRead])
async def get_notifications(
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[NotificationRead]:
    notifications: Sequence[Notification] = await NotificationRepository().list_by_user(session, current_user.id)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.patch("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    await NotificationRepository().mark_as_read(session, notification_id, current_user.id)


@router.post("/send", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def send_notification(
    data: NotificationCreate,
    session: AsyncSession = Depends(get_session_with_user),
) -> NotificationRead:
    notification = await NotificationRepository().create_read(session, data)
    return NotificationRead.model_validate(notification)
