# src/repositories/user.py
# from typing import Tuple

# from sqlalchemy import Result, select
# from sqlalchemy.ext.asyncio import AsyncSession

# from db.models import User


# class UserRepository:
#     def __init__(self, db: AsyncSession) -> None:
#         self.db: AsyncSession = db

#     async def get(self, user_id: int) -> User | None:
#         res: Result[Tuple[User]] = await self.db.execute(select(User).where(User.id == user_id))
#         return res.scalar_one_or_none()

#     async def create(self, **kwargs) -> User:
#         user = User(**kwargs)
#         self.db.add(user)
#         await self.db.flush()
#         return user
