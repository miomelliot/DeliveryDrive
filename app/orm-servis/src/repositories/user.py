from datetime import time
from pathlib import Path
from typing import Any
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import ScalarResult, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import CourierSchedule, Role, Transport, TransportType, User
from src.schemas.user import (
    UserCourierCreate,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerUpdate,
)

# где физически храним png
SAVE_DIR = Path("/app/static/icons")


# ─────────────────────────── Base ───────────────────────────
class UserBaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    # ---------- CRUD ----------
    async def get_all(self) -> list[User]:
        result: ScalarResult[User] = await self.session.scalars(select(User))
        return list(result.all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    # ---------- helpers ----------
    async def _get_role(self, name: str) -> Role:
        role: Role | None = await self.session.scalar(select(Role).where(Role.name == name))
        if not role:
            raise ValueError(f"Role '{name}' not found")
        return role

    async def _get_transport_type_id(self, name: str) -> int:
        tt: TransportType | None = await self.session.scalar(select(TransportType).where(TransportType.name == name))
        if not tt:
            raise ValueError(f"TransportType '{name}' not found")
        return tt.id

    async def _save_icon(self, user_id: UUID, icon: UploadFile) -> str:
        """Сохраняем файл /app/static/icons/<id>.png и возвращаем URL."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        file_path: Path = SAVE_DIR / f"{user_id}.png"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await icon.read())
        return f"/static/icons/{user_id}.png"


# ───────────────────────── Manager ─────────────────────────
class UserManagerRepository(UserBaseRepository):
    async def create(self, data: UserManagerCreate, icon: UploadFile | None) -> User:
        role: Role = await self._get_role("manager")
        user_id: UUID = uuid7()
        avatar: str | None = await self._save_icon(user_id, icon) if icon else None

        user = User(
            id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            avatar_path=avatar,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserManagerUpdate, icon: UploadFile | None) -> User | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["avatar_path"] = await self._save_icon(user_id, icon)

        if values:
            await self.session.execute(sa_update(User).where(User.id == user_id).values(**values))

        await self.session.commit()
        return await self.session.get(User, user_id)


# ───────────────────────── Courier ─────────────────────────
class UserCourierRepository(UserBaseRepository):
    async def create(self, data: UserCourierCreate, icon: UploadFile | None) -> User:
        role: Role = await self._get_role("courier")
        user_id: UUID = uuid7()
        avatar: str | None = await self._save_icon(user_id, icon) if icon else None

        user = User(
            id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=role.id,
            avatar_path=avatar,
        )
        self.session.add(user)
        await self.session.flush()

        self.session.add(
            CourierSchedule(
                courier_id=user_id,
                start_time=data.start_time,
                end_time=data.end_time,
            )
        )

        tt_id: int = await self._get_transport_type_id(data.transport_name)
        self.session.add(Transport(courier_id=user_id, transport_type_id=tt_id))

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserCourierUpdate, icon: UploadFile | None) -> User | None:
        base_values: dict[str, Any] = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"start_time", "end_time", "transport_name"},
        )
        if "password" in base_values:
            base_values["password_hash"] = hash_password(base_values.pop("password"))
        if icon:
            base_values["avatar_path"] = await self._save_icon(user_id, icon)

        # --- user -------------
        if base_values:
            await self.session.execute(sa_update(User).where(User.id == user_id).values(**base_values))

        # --- расписание -------
        if data.start_time is not None or data.end_time is not None:
            sched_vals: dict[str, time] = {
                k: v for k, v in {"start_time": data.start_time, "end_time": data.end_time}.items() if v is not None
            }
            await self.session.execute(
                sa_update(CourierSchedule).where(CourierSchedule.courier_id == user_id).values(**sched_vals)
            )

        # --- транспорт --------
        if data.transport_name:
            tt_id: int = await self._get_transport_type_id(data.transport_name)
            await self.session.execute(
                sa_update(Transport).where(Transport.courier_id == user_id).values(transport_type_id=tt_id)
            )

        await self.session.commit()
        return await self.session.get(User, user_id)
