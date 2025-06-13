# src/repositories/tables/event_type.py
from src.db.models import EventType
from src.repositories.tables.base_status import BaseStatusRepository


class EventTypeRepository(BaseStatusRepository[EventType]):
    def __init__(self) -> None:
        super().__init__(EventType)
