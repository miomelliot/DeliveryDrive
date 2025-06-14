# src/repositories/tables/equipment.py

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Equipment, HeaterType, Warehouse
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.equipment_status import EquipmentStatusRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.warehouse import WarehouseRepository
from src.schemas.equipment import EquipmentCreate, EquipmentCreateAPI, EquipmentUpdate
from src.schemas.heater_type import HeaterTypeCreate


class EquipmentRepository(CRUDRepository[Equipment, EquipmentCreate, EquipmentUpdate]):
    def __init__(self) -> None:
        super().__init__(Equipment)

    async def create_raw(self, session: AsyncSession, raw_data: EquipmentCreateAPI) -> Equipment:
        heater_type: HeaterType = await HeaterTypeRepository().create(
            session,
            HeaterTypeCreate(
                model=raw_data.model,
                price=raw_data.price,
                weight=raw_data.weight,
            ),
        )
        equipment_status_id: int = await EquipmentStatusRepository().get_id(session, "available")
        warehouse: Sequence[Warehouse] = await WarehouseRepository().list(session)
        obj_in = EquipmentCreate(
            heater_type_id=heater_type.id,
            serial_number=raw_data.serial_number,
            equipment_status_id=equipment_status_id,
            warehouse_id=warehouse[0].id,
            current_address_id=warehouse[0].address_id,
        )

        return await super().create(session, obj_in)

    async def create(self, session: AsyncSession, obj_in: EquipmentCreate) -> Equipment:
        return await super().create(session, obj_in)
