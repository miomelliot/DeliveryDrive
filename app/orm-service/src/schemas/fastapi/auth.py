# src/schemas/auth.py
from uuid import UUID

from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: UUID
    role: str
