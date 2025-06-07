# src/api/user.py
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.session import get_session
from src.repositories.user import UserRepository
from src.schemas.user import (
    UserCourierCreate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/courier", response_model=UserManagerRead)
async def create_courier_user(
    data: UserCourierCreate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserRepository(session)
    user: User = await repo.create_courier(data, icon)
    return UserManagerRead.model_validate(user)


@router.post("/manager", response_model=UserManagerRead)
async def create_manager_user(
    data: UserManagerCreate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserRepository(session)
    user: User = await repo.create_manager(data, icon)
    return UserManagerRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserManagerRead)
async def update_user(
    user_id: UUID,
    data: UserManagerUpdate = Depends(),
    icon: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
) -> UserManagerRead:
    repo = UserRepository(session)
    user: User | None = await repo.update(user_id, data, icon)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserManagerRead.model_validate(user)


@router.get("/", response_model=list[UserManagerRead])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserManagerRead]:
    repo = UserRepository(session)
    users: list[User] = await repo.get_all()
    return [UserManagerRead.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserManagerRead)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_session)) -> UserManagerRead:
    repo = UserRepository(session)
    user: User | None = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserManagerRead.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    repo = UserRepository(session)
    await repo.delete(user_id)
    return {"detail": "Пользователь удалён"}
