from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Tracking
from src.repositories.tables.base import CRUDRepository
from src.schemas.tracking import TrackingCreate, TrackingUpdate


class TrackingRepository(CRUDRepository[Tracking, TrackingCreate, TrackingUpdate]):
    def __init__(self) -> None:
        super().__init__(Tracking)

    async def create_raw(self, session: AsyncSession, raw_data: TrackingCreate) -> Tracking:
        obj_in = TrackingCreate(
            route_item_id=raw_data.route_item_id,
            event_type=raw_data.event_type,
            event_time=datetime.now(timezone.utc),
        )

        return await super().create(session, obj_in)
