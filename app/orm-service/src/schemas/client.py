# src/schemas/client.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _ClientBase(BaseModel):
    name: str
    phone: str | None


class ClientCreate(_ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str
    phone: str | None


class ClientRead(_ClientBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
