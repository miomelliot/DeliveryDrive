# src/api/user_chart.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.user_chart import UserChartRepository
from src.schemas.user_chart import UserChartFilter, UserChartRead

router = APIRouter(prefix="/charts/users", tags=["User Charts"])


@router.get("/", response_model=list[UserChartRead])
async def get_user_chart(
    filters: UserChartFilter = Depends(),
    session: AsyncSession = Depends(get_session),
) -> list[UserChartRead]:
    repo = UserChartRepository(session)
    return await repo.get_chart(filters)
