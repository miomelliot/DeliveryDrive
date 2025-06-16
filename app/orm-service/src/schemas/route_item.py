from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RouteItemCreate(BaseModel):
    route_id: UUID
    order_id: UUID


class RouteItemUpdate(BaseModel):
    pass


class RouteItemRead(BaseModel):
    id: UUID
    route_id: UUID
    order_id: UUID
    sequence: int

    model_config = ConfigDict(from_attributes=True)
