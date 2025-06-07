# src/api/equipment_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.equipment_chart import EquipmentChartRepository
from src.schemas.equipment_chart import EquipmentChartFilter, EquipmentChartRead

router = APIRouter(prefix="/charts/equipment", tags=["Equipment Chart"])


@router.get("/", response_model=list[EquipmentChartRead])
async def get_equipment_chart(
    filters: EquipmentChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> list[EquipmentChartRead]:
    repo = EquipmentChartRepository(session)
    return await repo.get_chart(filters)
