from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _TrackingBase(BaseModel):
    route_item_id: UUID
    event_type: str
    event_time: datetime | None = None


class TrackingCreateAPI(_TrackingBase):
    pass


class TrackingCreate(BaseModel):
    route_item_id: UUID
    event_type_id: int
    event_time: datetime


class TrackingUpdate(BaseModel):
    pass


class TrackingRead(TrackingCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class OrderLastEvent(BaseModel):
    order_id: UUID
    description: str | None
    model_config = ConfigDict(from_attributes=True)


class RouteLastEvent(BaseModel):
    route_id: UUID
    description: str | None
    model_config = ConfigDict(from_attributes=True)
