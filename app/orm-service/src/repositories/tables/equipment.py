# src/repositories/tables/equipment.py
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Equipment, HeaterType, Warehouse
from src.repositories.tables.base import CRUDRepository
from src.repositories.tables.equipment_status import EquipmentStatusRepository
from src.repositories.tables.heater_type import HeaterTypeRepository
from src.repositories.tables.warehouse import WarehouseRepository
from src.schemas.equipment import EquipmentCreate, EquipmentCreateAPI, EquipmentUpdate
from src.schemas.heater_type import HeaterTypeCreate
from src.utils.http_error import ConflictError


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
        equipment_status_id: int = await EquipmentStatusRepository().get_code_id(session, "available")
        warehouse: Sequence[Warehouse] = await WarehouseRepository().list(session)
        obj_in = EquipmentCreate(
            heater_type_id=heater_type.id,
            serial_number=raw_data.serial_number,
            equipment_status_id=equipment_status_id,
            warehouse_id=warehouse[0].id,
            current_address_id=warehouse[0].address_id,
        )

        return await super().create(session, obj_in)

    async def update_status_bulk(
        self,
        session: AsyncSession,
        *,
        heater_type_id: int,
        old_status_code: str,
        new_status_code: str,
        limit: int,
        model: str,
    ) -> list[Equipment]:
        status_repo = EquipmentStatusRepository()
        old_status_id: int = await status_repo.get_code_id(session, old_status_code)
        new_status_id: int = await status_repo.get_code_id(session, new_status_code)

        stmt: Select[Tuple[Equipment]] = (
            select(Equipment)
            .where(Equipment.heater_type_id == heater_type_id)
            .where(Equipment.equipment_status_id == old_status_id)
            .limit(limit)
        )
        res: Result[Tuple[Equipment]] = await session.execute(stmt)
        equipment_list: Sequence[Equipment] = res.scalars().all()

        if len(equipment_list) < limit:
            raise ConflictError(f"Недостаточно оборудования модели '{model}' на складе")

        for eq in equipment_list:
            eq.equipment_status_id = new_status_id

        await session.flush()
        return list(equipment_list)

    async def update_status(self, session: AsyncSession, id: UUID | int, status: str) -> Equipment:
        equipment_status_id: int = await EquipmentStatusRepository().get_code_id(session, status)
        obj_in = EquipmentUpdate(equipment_status_id=equipment_status_id)
        return await super().update_by_id(session, id, obj_in)
