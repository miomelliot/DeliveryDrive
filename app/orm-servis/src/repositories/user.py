# src/repositories/user.py
from datetime import time
from typing import Any, Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import ScalarResult, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import Role, User
from src.schemas.user import UserCourierCreate, UserManagerCreate, UserManagerUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_all(self) -> list[User]:
        result: ScalarResult[User] = await self.session.scalars(select(User))
        return list(result.all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create_courier(self, data: UserCourierCreate, icon: UploadFile | None) -> User:
        return await self._create_user(
            data=data,
            icon=icon,
            role_name="courier",
            start_time=data.start_time,
            end_time=data.end_time,
            transport_name=data.transport_name,
        )

    async def create_manager(self, data: UserManagerCreate, icon: UploadFile | None) -> User:
        return await self._create_user(
            data=data,
            icon=icon,
            role_name="manager",
        )

    async def _create_user(
        self,
        data: UserManagerCreate | UserCourierCreate,
        icon: UploadFile | None,
        role_name: str,
        start_time: time | None = None,
        end_time: time | None = None,
        transport_name: str | None = None,
    ) -> User:
        role: Role | None = await self._get_role_by_name(role_name)
        if role is None:
            raise ValueError(f"Роль '{role_name}' не найдена")

        user_id: UUID = uuid7()
        icon_path: str | None = await self.save_user_icon(user_id, icon) if icon else None

        user = User(
            id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role_id=role.id,
            start_time=start_time,
            end_time=end_time,
            transport_name=transport_name,
            icon=icon_path,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserManagerUpdate, icon: UploadFile | None = None) -> User | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)

        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))

        if icon:
            icon_path: str = await self.save_user_icon(user_id, icon)
            values["icon"] = icon_path

        stmt: ReturningUpdate[Tuple[User]] = sa_update(User).where(User.id == user_id).values(**values).returning(User)
        result: User | None = await self.session.scalar(stmt)
        await self.session.commit()
        return result

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    async def _get_role_by_name(self, role_name: str) -> Role | None:
        result: ScalarResult[Role] = await self.session.scalars(select(Role).where(Role.name == role_name))
        return result.first()

    async def save_user_icon(self, user_id: UUID, icon: UploadFile) -> str:
        filename: str = f"{user_id}.png"
        path: str = f"/static/icons/{filename}"

        async with aiofiles.open(path, "wb") as out_file:
            content: bytes = await icon.read()
            await out_file.write(content)

        return path
