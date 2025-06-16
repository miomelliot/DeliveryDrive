from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Tracking
from src.dependencies.db import get_session_with_user
from src.repositories.tables.tracking import TrackingRepository
from src.schemas.tracking import RouteLastEvent, TrackingCreateAPI, TrackingRead

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post("/", response_model=TrackingRead, status_code=201)
async def create_tracking(
    data: TrackingCreateAPI,
    session: AsyncSession = Depends(get_session_with_user),
) -> TrackingRead:
    tracking: Tracking = await TrackingRepository().create_raw(session, data)
    return TrackingRead.model_validate(tracking)


@router.get("/route/{route_id}", response_model=RouteLastEvent)
async def get_last_event(
    route_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> RouteLastEvent:
    description: str | None = await TrackingRepository().get_last_event_description(session, route_id)
    return RouteLastEvent(route_id=route_id, description=description)
