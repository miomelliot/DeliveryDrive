from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    user_id: UUID
    text: str


class NotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
