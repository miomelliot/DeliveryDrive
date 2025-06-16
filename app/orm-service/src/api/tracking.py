from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Tracking
from src.dependencies.db import get_session_with_user
from src.repositories.tables.tracking import TrackingRepository
from src.schemas.tracking import OrderLastEvent, TrackingCreate, TrackingRead

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post("/", response_model=TrackingRead, status_code=201)
async def create_tracking(
    data: TrackingCreate,
    session: AsyncSession = Depends(get_session_with_user),
) -> TrackingRead:
    tracking: Tracking = await TrackingRepository().create_raw(session, data)
    return TrackingRead.model_validate(tracking)


@router.get("/order/{order_id}", response_model=OrderLastEvent)
async def get_last_event(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> OrderLastEvent:
    description: str | None = await TrackingRepository().get_last_event_description(session, order_id)
    return OrderLastEvent(order_id=order_id, description=description)
