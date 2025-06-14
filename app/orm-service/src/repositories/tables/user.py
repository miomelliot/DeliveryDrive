# # src/repositories/tables/user.py
# from pathlib import Path
# from sqlite3 import IntegrityError
# from uuid import UUID

# import aiofiles
# from fastapi import UploadFile
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from src.core.security import hash_password
# from src.db.models import Role, User
# from src.repositories.tables.base import CRUDRepository
# from src.schemas.user import (
#     UserCreate,
#     UserManagerCreateAPI,
#     UserUpdate,
#     UserUpdateAPI,
# )
# from src.utils.http_error import ConflictError, InternalServerError, NotFoundError

# SAVE_DIR = Path("/app/static/icons")


# class UserBaseRepository:
#     async def _get_role(self, session: AsyncSession, name: str) -> Role:
#         role: Role | None = await session.scalar(select(Role).where(Role.name == name))
#         if role is None:
#             raise NotFoundError()
#         return role

#     async def _save_icon(self, user_id: UUID, avatar_path: UploadFile) -> str:
#         """Сохраняем файл /app/static/icons/<id>.png и возвращаем URL."""
#         SAVE_DIR.mkdir(parents=True, exist_ok=True)
#         file_path: Path = SAVE_DIR / f"{user_id}.png"
#         async with aiofiles.open(file_path, "wb") as f:
#             await f.write(await avatar_path.read())
#         return f"/static/icons/{user_id}.png"


# class UserManagerRepository(UserBaseRepository, CRUDRepository[User, UserCreate, UserUpdate]):
#     def __init__(self) -> None:
#         super().__init__(User)

#     async def create_extended(
#         self,
#         session: AsyncSession,
#         raw_data: UserManagerCreateAPI,
#         avatar_path: UploadFile | None,
#     ) -> User:
#         role: Role = await super()._get_role(session, "manager")

#         obj_in = UserCreate(
#             first_name=raw_data.first_name,
#             last_name=raw_data.last_name,
#             phone=raw_data.phone,
#             email=raw_data.email,
#             password_hash=hash_password(raw_data.password),
#             role_id=role.id,
#         )

#         try:
#             user: User = await super().create(session, obj_in)
#         except IntegrityError as err:
#             if "email" in str(err):
#                 raise ConflictError(f"Email уже используется: {obj_in.email}") from err
#             raise InternalServerError() from err

#         if avatar_path:
#             await super()._save_icon(user.id, avatar_path)

#         return user

#     async def update_by_id_extended(
#         self, session: AsyncSession, id: UUID, raw_data: UserUpdateAPI, avatar_path: UploadFile | None
#     ) -> User:
#         if raw_data.password:
#             raw_data.password = hash_password(raw_data.password)

#         obj_in = UserUpdate(
#             first_name=raw_data.first_name,
#             last_name=raw_data.last_name,
#             phone=raw_data.phone,
#             email=raw_data.email,
#             password_hash=raw_data.password,
#         )

#         if avatar_path:
#             await super()._save_icon(id, avatar_path)
#         return await super().update_by_id(session, id, obj_in)
