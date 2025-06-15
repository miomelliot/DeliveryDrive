# src/api/user_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.dependencies.db import get_session_with_user
from src.repositories.charts.user_chart import UserChartRepository
from src.schemas.auth import CurrentUser
from src.schemas.user_chart import UserChartFilter, UserChartRead

router = APIRouter(prefix="/charts/users", tags=["User Chart"])


@router.get("/", response_model=list[UserChartRead])
async def get_user_chart(
    filters: UserChartFilter = Depends(),
    session: AsyncSession = Depends(get_session_with_user),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[UserChartRead]:
    repo = UserChartRepository(session)
    return await repo.get_chart(filters)
