from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.tables.tracking import TrackingRepository
from src.schemas.tracking import RouteLastEvent, TrackingCreateAPI

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tracking(
    data: TrackingCreateAPI,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await TrackingRepository().create_raw(session, data)
    return {"detail": "Событие добавленно"}


@router.get("/route/{route_id}", response_model=RouteLastEvent)
async def get_last_event(
    route_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> RouteLastEvent:
    description: str | None = await TrackingRepository().get_last_event_description(session, route_id)
    return RouteLastEvent(route_id=route_id, description=description)
