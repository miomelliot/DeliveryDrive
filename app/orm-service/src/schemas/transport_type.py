# src/schemas/transport_type.py
from pydantic import BaseModel, ConfigDict, Field


class _TransportTypeBase(BaseModel):
    name: str
    avg_speed: float = Field(..., ge=0, examples=[60.0])
    capacity: float = Field(..., ge=0, examples=[1200.0])


class TransportTypeCreate(_TransportTypeBase):
    pass


class TransportTypeUpdate(BaseModel):
    name: str | None = None
    avg_speed: float | None = Field(None, ge=0)
    capacity: float | None = Field(None, ge=0)


class TransportTypeRead(_TransportTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
