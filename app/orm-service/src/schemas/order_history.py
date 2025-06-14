from uuid import UUID

from pydantic import BaseModel


class _OrderHistoryBase(BaseModel):
    order_id: UUID
    new_status_id: int
    previous_status_id: int | None = None
    user_id: UUID | None = None


class OrderHistoryCreate(_OrderHistoryBase):
    pass


class OrderHistoryUpdate(BaseModel):
    pass
