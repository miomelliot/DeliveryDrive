# src/schemas/client.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.address import AddressCreate, AddressRead


class _ClientBase(BaseModel):
    name: str
    phone: str


class ClientCreate(_ClientBase):
    location: AddressCreate


class ClientUpdate(BaseModel):
    name: str | None
    phone: str | None
    location: AddressCreate | None


class ClientRead(_ClientBase):
    id: UUID
    address: AddressRead
    model_config = ConfigDict(from_attributes=True)
