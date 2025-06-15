# src/schemas/heater_type.py
from pydantic import BaseModel, ConfigDict, Field


class _HeaterTypeBase(BaseModel):
    model: str
    price: float = Field(..., ge=0, examples=[599.0])
    weight: float = Field(..., ge=0, examples=[2.0])


class HeaterTypeCreate(_HeaterTypeBase):
    pass


class HeaterTypeUpdate(BaseModel):
    model: str | None = None
    price: float | None = Field(None, ge=0)
    weight: float | None = Field(None, ge=0)


class HeaterTypeRead(_HeaterTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
