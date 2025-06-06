# src/repositories/equipment_chart.py
from datetime import date
from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy import Result, String, func, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.db.models import Address, Equipment, EquipmentStatus, HeaterType, Maintenance
from src.schemas.equipment_chart import EquipmentChartFilter, EquipmentChartRead
from src.utils.sqlalchemy_expr import location_expr


class EquipmentChartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_chart(self, filters: EquipmentChartFilter) -> list[EquipmentChartRead]:
        # 📋 Базовый SELECT
        stmt: Select[Tuple[UUID, date, str, float, float, str, str]] = (
            select(
                Equipment.id,
                Maintenance.date,
                HeaterType.model,
                HeaterType.weight,
                HeaterType.price,
                location_expr(),
                EquipmentStatus.description.label("status"),
            )
            .join(Maintenance, Maintenance.equipment_id == Equipment.id)
            .join(HeaterType, HeaterType.id == Equipment.heater_type_id)
            .join(Address, Address.id == Equipment.current_address_id)
            .join(EquipmentStatus, EquipmentStatus.id == Equipment.equipment_status_id)
        )

        # 🔍 Поиск
        if filters.search:
            like: str = f"%{filters.search.lower()}%"
            stmt = stmt.where(
                func.lower(HeaterType.model).like(like)
                | func.cast(HeaterType.weight, String).like(like)
                | func.cast(HeaterType.price, String).like(like)
                | func.lower(location_expr()).like(like)
                | func.lower(EquipmentStatus.description).like(like)
            )

        # 📅 Диапазон дат обслуживания
        if filters.date_start:
            stmt = stmt.where(Maintenance.date >= filters.date_start)
        if filters.date_end:
            stmt = stmt.where(Maintenance.date <= filters.date_end)

        # ↕️ Сортировка
        field_map = {
            "id": Equipment.id,
            "model": HeaterType.model,
            "weight": HeaterType.weight,
            "price": HeaterType.price,
            "location": location_expr(),
            "status": EquipmentStatus.description,
        }
        sort_col = field_map.get(filters.order_by, Equipment.id)
        stmt = stmt.order_by(sort_col.desc() if filters.order_dir == "desc" else sort_col.asc())

        # 📄 Пагинация
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        # 🧾 Выполнение запроса
        res: Result[Tuple[UUID, date, str, float, float, str, str]] = await self.session.execute(stmt)
        rows: Sequence[Row[Tuple[UUID, date, str, float, float, str, str]]] = res.fetchall()

        return [EquipmentChartRead.model_validate(r._asdict()) for r in rows]
