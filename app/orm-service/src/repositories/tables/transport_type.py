# src/repositories/tables/transport_type.py
from src.db.models import TransportType
from src.schemas.transport_type import (
    TransportTypeCreate,
    TransportTypeUpdate,
)

from .base import CRUDRepository


class TransportTypeRepository(CRUDRepository[TransportType, TransportTypeCreate, TransportTypeUpdate]):
    def __init__(self) -> None:
        super().__init__(TransportType)

    # Здесь можно добавить кастомные методы,
    # например list_by_capacity(...) или search_by_name(...)
