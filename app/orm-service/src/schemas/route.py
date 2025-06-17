from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.order_detail_read import OrderDetailRead


class RouteRead(BaseModel):
    id: UUID
    courier_id: UUID
    date: dt_date
    planned_start: datetime
    planned_end: datetime
    model_config = ConfigDict(from_attributes=True)


class RouteItemStatus(BaseModel):
    id: UUID
    order: OrderDetailRead
    sequence: int
    status: str | None = None
    model_config = ConfigDict(from_attributes=True)


class RouteCreate(BaseModel):
    courier_id: UUID
    date: dt_date
    planned_start: datetime
    planned_end: datetime


class RouteUpdate(BaseModel):
    courier_id: UUID | None = None
    date: dt_date | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
