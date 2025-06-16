# src/schemas/address.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AddressRead(BaseModel):
    id: UUID
    city: str
    street: str | None
    building: str
    lat: float = 0.0
    lon: float = 0.0
    model_config = ConfigDict(from_attributes=True)
