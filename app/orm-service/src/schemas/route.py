from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RouteRead(BaseModel):
    id: UUID
    courier_id: UUID
    date: date
    planned_start: datetime
    planned_end: datetime
    model_config = ConfigDict(from_attributes=True)


class RouteItemStatus(BaseModel):
    id: UUID
    order_id: UUID | None
    sequence: int
    status: str | None = None
    model_config = ConfigDict(from_attributes=True)
