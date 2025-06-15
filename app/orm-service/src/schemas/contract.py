# src/schemas/contract.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _ContractBase(BaseModel):
    order_id: UUID
    file_path: str


class ContractCreate(_ContractBase):
    pass


class ContractUpdate(BaseModel):
    pass


class ContractRead(_ContractBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
