from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Notification
from src.dependencies.auth import get_current_user
from src.dependencies.db import get_session_with_user
from src.repositories.notification import NotificationRepository
from src.schemas.auth import CurrentUser
from src.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/unread", response_model=list[NotificationRead])
async def get_unread_notifications(
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[NotificationRead]:
    repo = NotificationRepository()
    notifications: Sequence[Notification] = await repo.list_unread_by_user(session, current_user.id)
    if notifications:
        await repo.mark_all_as_read(session, current_user.id)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/unread_count", response_model=int)
async def unread_count(
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> int:
    return await NotificationRepository().count_unread_by_user(session, current_user.id)
