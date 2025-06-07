# src/api/user.py
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.session import get_session
from src.repositories.user import UserCourierRepository, UserManagerRepository
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

router = APIRouter(prefix="/user", tags=["User"])


# ─────────────────────────── MANAGER ───────────────────────────
@router.post("/manager", response_model=UserManagerRead)
async def create_manager_user(
    data: UserManagerCreate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    user: User = await repo.create(data, icon)
    return UserManagerRead.model_validate(user)


@router.patch("/manager/{user_id}", response_model=UserManagerRead)
async def update_manager_user(
    user_id: UUID,
    data: UserManagerUpdate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserManagerRepository(session)
    user: User | None = await repo.update(user_id, data, icon)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserManagerRead.model_validate(user)


@router.get("/manager", response_model=list[UserManagerRead])
async def list_managers(session: AsyncSession = Depends(get_session)) -> list[UserManagerRead]:
    repo = UserManagerRepository(session)
    users: list[User] = await repo.get_all()
    return [UserManagerRead.model_validate(u) for u in users]


@router.get("/manager/{user_id}", response_model=UserManagerRead)
async def get_manager(user_id: UUID, session: AsyncSession = Depends(get_session)) -> UserManagerRead:
    repo = UserManagerRepository(session)
    user: User | None = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserManagerRead.model_validate(user)


# ─────────────────────────── COURIER ───────────────────────────
@router.post("/courier", response_model=UserCourierRead)
async def create_courier_user(
    data: UserCourierCreate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    user: User = await repo.create(data, icon)
    return UserCourierRead.model_validate(user)


@router.patch("/courier/{user_id}", response_model=UserCourierRead)
async def update_courier_user(
    user_id: UUID,
    data: UserCourierUpdate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserCourierRead:
    repo = UserCourierRepository(session)
    user: User | None = await repo.update(user_id, data, icon)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserCourierRead.model_validate(user)


@router.get("/courier", response_model=list[UserCourierRead])
async def list_couriers(session: AsyncSession = Depends(get_session)) -> list[UserCourierRead]:
    repo = UserCourierRepository(session)
    users: list[User] = await repo.get_all()
    return [UserCourierRead.model_validate(u) for u in users]


@router.get("/courier/{user_id}", response_model=UserCourierRead)
async def get_courier(user_id: UUID, session: AsyncSession = Depends(get_session)) -> UserCourierRead:
    repo = UserCourierRepository(session)
    user: User | None = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserCourierRead.model_validate(user)


# ─────────────────────────── DELETE ───────────────────────────
@router.delete("/{user_id}")
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    # Можно удалить любого пользователя — по ID
    repo = UserManagerRepository(session)  # или UserBaseRepository(session)
    await repo.delete(user_id)
    return {"detail": "Пользователь удалён"}
