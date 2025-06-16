from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.order_detail_read import OrderDetailRead


class RouteRead(BaseModel):
    id: UUID
    courier_id: UUID
    date: date
    planned_start: datetime
    planned_end: datetime
    model_config = ConfigDict(from_attributes=True)


class RouteItemStatus(BaseModel):
    id: UUID
    order: OrderDetailRead
    sequence: int
    status: str | None = None
    model_config = ConfigDict(from_attributes=True)
