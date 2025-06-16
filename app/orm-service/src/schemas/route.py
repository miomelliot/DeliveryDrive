# src/schemas/route.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _RouteBase(BaseModel):
    pass


class RouteCreate(_RouteBase):
    pass


class RouteUpdate(BaseModel):
    pass


class RouteRead(_RouteBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
