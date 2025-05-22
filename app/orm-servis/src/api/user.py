# src/api/user.py
# from typing import Annotated

# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession

# from db.models import User
# from db.session import get_session
# from repositories.user import UserRepository
# from schemas.user import UserCreate, UserRead

# # ── Глобальная зависимость с точным типом ─────────────────────────────────────
# DbSessionDep = Annotated[AsyncSession, Depends(get_session)]

# router = APIRouter(prefix="/users", tags=["Users"])


# @router.post("/", response_model=UserRead, status_code=201)
# async def create_user(
#     payload: UserCreate,
#     db: DbSessionDep,
# ) -> UserRead:
#     repo = UserRepository(db)
#     orm_user: User = await repo.create(**payload.model_dump())
#     await db.commit()
#     return UserRead.model_validate(orm_user)
