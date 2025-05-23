from typing import Optional, Sequence, Tuple
from uuid import UUID

from passlib.hash import bcrypt
from sqlalchemy import ScalarResult, Select, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate
from uuid6 import uuid7

from src.db.models import User
from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        # Асинхронная сессия SQLAlchemy передаётся из Depends
        self.session: AsyncSession = session

    async def get_all(self) -> Sequence[User]:
        #! Получаем список всех пользователей из таблицы user
        result: ScalarResult[User] = await self.session.scalars(select(User))
        return result.all()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        # Получаем одного пользователя по его UUID (PK)
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        # Получаем пользователя по email (нужно для логина)
        stmt: Select[Tuple[User]] = select(User).where(User.email == email)
        result: ScalarResult[User] = await self.session.scalars(stmt)
        return result.first()

    async def create(self, data: UserCreate) -> User:
        # Создаём пользователя на основе UserCreate
        user = User(
            id=uuid7(),
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            avatar_path=data.avatar_path,
            password_hash=self._hash_pwd(data.password),
            role_id=data.role_id,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)  # обновляем объект после вставки
        return user

    async def update(self, user_id: UUID, data: UserUpdate) -> Optional[User]:
        # Обновление пользователя по его ID
        stmt: ReturningUpdate[Tuple[User]] = (
            sa_update(User)
            .where(User.id == user_id)
            .values(**data.model_dump(exclude_none=True))  # обновляем только переданные поля
            .returning(User)  # вернёт обновлённый объект
        )
        result: User | None = await self.session.scalar(stmt)
        await self.session.commit()
        return result

    async def delete(self, user_id: UUID) -> None:
        # Удаление пользователя по UUID
        await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.commit()

    # 🔒 Приватный метод для хеширования пароля
    @staticmethod
    def _hash_pwd(raw: str) -> str:
        return str(bcrypt.hash(raw))
