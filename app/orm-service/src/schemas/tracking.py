from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _TrackingBase(BaseModel):
    route_item_id: UUID
    event_type_id: int
    event_time: datetime


class TrackingCreate(_TrackingBase):
    pass


class TrackingUpdate(BaseModel):
    pass


class TrackingRead(_TrackingBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class OrderLastEvent(BaseModel):
    order_id: UUID
    description: str | None
    model_config = ConfigDict(from_attributes=True)
