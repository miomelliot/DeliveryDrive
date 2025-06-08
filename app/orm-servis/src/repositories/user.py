from datetime import time
from pathlib import Path
from typing import Any, Tuple
from uuid import UUID

import aiofiles
from fastapi import UploadFile
from sqlalchemy import Result, ScalarResult, Select, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.core.security import hash_password
from src.db.models import CourierSchedule, Role, Transport, TransportType, User
from src.schemas.user import (
    UserCourierCreate,
    UserCourierRead,
    UserCourierUpdate,
    UserManagerCreate,
    UserManagerRead,
    UserManagerUpdate,
)

# где физически храним png
SAVE_DIR = Path("/app/static/icons")


# ─────────────────────────── Base ───────────────────────────
class UserBaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    # ---------- CRUD ----------
    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    # ---------- helpers ----------
    async def _get_role(self, name: str) -> Role:
        role: Role | None = await self.session.scalar(select(Role).where(Role.name == name))
        if not role:
            raise ValueError(f"Role '{name}' not found")
        return role

    async def _get_transport_type(self, name: str) -> TransportType:
        tt: TransportType | None = await self.session.scalar(select(TransportType).where(TransportType.name == name))
        if not tt:
            raise ValueError(f"TransportType '{name}' not found")
        return tt

    async def _save_icon(self, user_id: UUID, icon: UploadFile) -> str:
        """Сохраняем файл /app/static/icons/<id>.png и возвращаем URL."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        file_path: Path = SAVE_DIR / f"{user_id}.png"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await icon.read())
        return f"/static/icons/{user_id}.png"


# ───────────────────────── Manager ─────────────────────────
class UserManagerRepository(UserBaseRepository):
    # ---------- CREATE ----------
    async def create(self, data: UserManagerCreate, icon: UploadFile | None) -> UserManagerRead:
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

        return UserManagerRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )

    # ---------- UPDATE ----------
    async def update(self, user_id: UUID, data: UserManagerUpdate, icon: UploadFile | None) -> UserManagerRead | None:
        values: dict[str, Any] = data.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["avatar_path"] = await self._save_icon(user_id, icon)

        if values:
            await self.session.execute(sa_update(User).where(User.id == user_id).values(**values))
            await self.session.commit()

        user: User | None = await self.session.get(User, user_id)
        if not user:
            return None
        return UserManagerRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )

    # ----------- list -----------
    async def list(self) -> list[UserManagerRead]:
        rows: ScalarResult[User] = await self.session.scalars(select(User))
        return [
            UserManagerRead(
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                avatar_path=user.avatar_path,
            )
            for user in rows
        ]

    # ----------- GET -----------
    async def get(self, user_id: UUID) -> UserManagerRead | None:
        user: User | None = await self.session.get(User, user_id)
        if not user:
            return None
        return UserManagerRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
        )


# ───────────────────────── Courier ─────────────────────────
class UserCourierRepository(UserBaseRepository):
    # ---------- CREATE ----------
    async def create(self, data: UserCourierCreate, icon: UploadFile | None) -> UserCourierRead:
        role: Role = await self._get_role("courier")
        user_id: UUID = uuid7()
        avatar: str | None = await self._save_icon(user_id, icon) if icon else None

        # 1. user
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
        await self.session.flush()  # нужен ID для внешних ключей

        # 2. schedule
        self.session.add(
            CourierSchedule(
                courier_id=user_id,
                start_time=data.start_time,
                end_time=data.end_time,
            )
        )

        # 3. transport
        tt: TransportType = await self._get_transport_type(data.transport_name)
        self.session.add(Transport(courier_id=user_id, transport_type_id=tt.id))

        await self.session.commit()
        # DTO
        return UserCourierRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=data.start_time,
            end_time=data.end_time,
            transport_name=tt.name,  # type: ignore
        )

    # ---------- UPDATE ----------
    async def update(self, user_id: UUID, data: UserCourierUpdate, icon: UploadFile | None) -> UserCourierRead | None:  # noqa: C901
        values: dict[str, Any] = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"start_time", "end_time", "transport_name"},
        )

        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        if icon:
            values["avatar_path"] = await self._save_icon(user_id, icon)

        if values:
            await self.session.execute(sa_update(User).where(User.id == user_id).values(**values))

        # Обновляем расписание, если есть
        if data.start_time is not None or data.end_time is not None:
            sched_vals: dict[str, time] = {
                k: v
                for k, v in {
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                }.items()
                if v is not None
            }
            await self.session.execute(
                sa_update(CourierSchedule).where(CourierSchedule.courier_id == user_id).values(**sched_vals)
            )

        # Объявляем переменную заранее
        transport_name: str

        # Обновляем тип транспорта
        if data.transport_name:
            transport_type_new: TransportType = await self._get_transport_type(data.transport_name)
            await self.session.execute(
                sa_update(Transport)
                .where(Transport.courier_id == user_id)
                .values(transport_type_id=transport_type_new.id)
            )
            transport_name = transport_type_new.name
        else:
            transport_type_existing: TransportType | None = await self.session.scalar(
                select(TransportType)
                .join(Transport, Transport.transport_type_id == TransportType.id)
                .where(Transport.courier_id == user_id)
            )
            if transport_type_existing is None:
                raise ValueError(f"Тип транспорта не найден для курьера с ID: {user_id}")
            transport_name = transport_type_existing.name

        await self.session.commit()

        user: User | None = await self.session.get(User, user_id)
        if not user:
            return None

        sched: CourierSchedule | None = await self.session.scalar(
            select(CourierSchedule).where(CourierSchedule.courier_id == user_id)
        )
        if sched is None:
            raise ValueError(f"Не найдено расписание курьера с ID: {user_id}")

        return UserCourierRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=sched.start_time,
            end_time=sched.end_time,
            transport_name=transport_name,  # type: ignore
        )

    # ----------- list -----------
    async def list(self) -> list[UserCourierRead]:
        stmt: Select[Tuple[User, CourierSchedule, str]] = (
            select(User, CourierSchedule, TransportType.name)
            .join(CourierSchedule, CourierSchedule.courier_id == User.id)
            .join(Transport, Transport.courier_id == User.id)
            .join(TransportType, Transport.transport_type_id == TransportType.id)
        )
        rows: Result[Tuple[User, CourierSchedule, str]] = await self.session.execute(stmt)
        result: list[UserCourierRead] = []
        for user, sched, tt_name in rows:
            result.append(
                UserCourierRead(
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=user.phone,
                    email=user.email,
                    avatar_path=user.avatar_path,
                    start_time=sched.start_time,
                    end_time=sched.end_time,
                    transport_name=tt_name,
                )
            )
        return result

    # ------------- GET -------------
    async def get(self, user_id: UUID) -> UserCourierRead | None:
        user: User | None = await self.session.get(User, user_id)
        if not user:
            return None
        sched: CourierSchedule | None = await self.session.scalar(
            select(CourierSchedule).where(CourierSchedule.courier_id == user_id)
        )
        tt_name: str | None = await self.session.scalar(
            select(TransportType.name)
            .join(Transport, Transport.transport_type_id == TransportType.id)
            .where(Transport.courier_id == user_id)
        )
        return UserCourierRead(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            start_time=sched.start_time,  # type: ignore
            end_time=sched.end_time,  # type: ignore
            transport_name=tt_name,  # type: ignore
        )
