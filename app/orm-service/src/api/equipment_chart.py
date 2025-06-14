# src/api/equipment_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.dependencies.db import get_session_with_user
from src.repositories.charts.equipment_chart import EquipmentChartRepository
from src.schemas.auth import CurrentUser
from src.schemas.equipment_chart import EquipmentChartFilter, EquipmentChartRead

router = APIRouter(prefix="/charts/equipment", tags=["Equipment Chart"])


@router.get("/", response_model=list[EquipmentChartRead])
async def get_equipment_chart(
    filters: EquipmentChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[EquipmentChartRead]:
    repo = EquipmentChartRepository(session)
    return await repo.get_chart(filters)
