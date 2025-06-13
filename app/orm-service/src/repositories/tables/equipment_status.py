# src/repositories/tables/equipment_status.py
from src.db.models import EquipmentStatus
from src.repositories.tables.base_status import BaseStatusRepository


class EquipmentStatusRepository(BaseStatusRepository[EquipmentStatus]):
    def __init__(self) -> None:
        super().__init__(EquipmentStatus)
