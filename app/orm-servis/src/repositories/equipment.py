# src/repositories/equipment.py
from datetime import date
from typing import Tuple
from uuid import UUID

from sqlalchemy import ScalarResult, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.db.models import Equipment, EquipmentStatus, HeaterType
from src.schemas.equipment import EquipmentCreate, EquipmentFilter


class EquipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def add_equipment(self, data: EquipmentCreate) -> Equipment:
        heater_type: HeaterType | None = await self.session.scalar(
            select(HeaterType).where(HeaterType.model == data.model)
        )
        if not heater_type:
            raise ValueError(f"Модель '{data.model}' не найдена")

        status_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "in_stock")
        )

        equipment = Equipment(
            id=uuid7(),
            serial_number=data.serial_number,
            heater_type_id=heater_type.id,
            price=data.price,
            weight=data.weight,
            status_id=status_id,
        )

        self.session.add(equipment)
        await self.session.commit()
        await self.session.refresh(equipment)
        return equipment

    async def list_models_by_status(self, filter: EquipmentFilter) -> list[str]:
        stmt: Select[Tuple[str]] = select(HeaterType.model).join(Equipment).join(EquipmentStatus)

        if filter.status:
            stmt = stmt.where(EquipmentStatus.code == filter.status)

        stmt = stmt.distinct()
        result: ScalarResult[str] = await self.session.scalars(stmt)
        return list(result)

    async def delete_equipment(self, equipment_id: UUID) -> None:
        await self.session.execute(delete(Equipment).where(Equipment.id == equipment_id))
        await self.session.commit()

    async def decommission_equipment(self, equipment_id: UUID) -> None:
        status_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "decommissioned")
        )
        await self.session.execute(update(Equipment).where(Equipment.id == equipment_id).values(status_id=status_id))
        await self.session.commit()

    async def send_to_service(self, equipment_id: UUID) -> None:
        # Получаем ID нужных статусов
        available_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "available")
        )
        maintenance_id: int | None = await self.session.scalar(
            select(EquipmentStatus.id).where(EquipmentStatus.code == "maintenance")
        )

        if available_id is None or maintenance_id is None:
            raise ValueError("Не найдены необходимые статусы оборудования")

        # Получаем текущий статус оборудования
        current_status_id: int | None = await self.session.scalar(
            select(Equipment.equipment_status_id).where(Equipment.id == equipment_id)
        )

        if current_status_id is None:
            raise ValueError("Оборудование не найдено")

        # Переключение статуса
        if current_status_id == available_id:
            # Отправляем на обслуживание
            await self.session.execute(
                update(Equipment)
                .where(Equipment.id == equipment_id)
                .values(
                    equipment_status_id=maintenance_id,
                    service_start=date.today(),
                )
            )
        elif current_status_id == maintenance_id:
            # Возвращаем в доступность
            await self.session.execute(
                update(Equipment)
                .where(Equipment.id == equipment_id)
                .values(
                    equipment_status_id=available_id,
                    service_start=None,
                )
            )
        else:
            raise ValueError("Оборудование должно быть в статусе 'available' или 'maintenance'")

        await self.session.commit()
