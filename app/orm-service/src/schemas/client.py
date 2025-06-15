# src/schemas/client.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.address import AddressRead


class _ClientBase(BaseModel):
    name: str | None
    phone: str


class ClientCreate(_ClientBase):
    address_id: UUID


class ClientUpdate(BaseModel):
    name: str | None
    phone: str | None


class ClientRead(_ClientBase):
    id: UUID
    address: AddressRead
    model_config = ConfigDict(from_attributes=True)
