# src/schemas/base_lookup.py
from pydantic import BaseModel, ConfigDict


class _BaseLookup(BaseModel):
    code: str
    description: str


class BaseLookupCreate(_BaseLookup):
    pass


class BaseLookupUpdate(BaseModel):
    code: str | None
    description: str | None


class BaseLookupRead(_BaseLookup):
    id: int
    model_config = ConfigDict(from_attributes=True)
