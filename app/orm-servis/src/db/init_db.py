# # src/db/init_db.py
# from __future__ import annotations

# import asyncio
# from typing import Any, Sequence

# import typer
# from passlib.hash import bcrypt
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from uuid6 import uuid7

# from core.config import Settings
# from src.core.config import get_settings
# from src.db.models import (
#     Base,
#     EquipmentStatus,
#     EventType,
#     HeaterType,
#     InvoiceStatus,
#     OrderStatus,
#     Role,
#     TransportType,
#     User,
# )
# from src.db.session import AsyncSessionFactory, engine

# app = typer.Typer(help="DB bootstrap & seed utility")

# # ---- справочники по умолчанию ------------------------------------------------
# REF_DATA: dict[Any, list[dict[str, str | int | float]]] = {
#     Role: [
#         {"id": 1, "name": "admin"},
#         {"id": 2, "name": "courier"},
#         {"id": 3, "name": "manager"},
#     ],
#     OrderStatus: [
#         {"id": 1, "code": "new", "description": "Создан"},
#         {"id": 2, "code": "in_progress", "description": "В работе"},
#         {"id": 3, "code": "done", "description": "Выполнен"},
#     ],
#     EquipmentStatus: [
#         {"id": 1, "code": "ready", "description": "Готов к аренде"},
#         {"id": 2, "code": "maintenance", "description": "Требует ТО"},
#     ],
#     InvoiceStatus: [
#         {"id": 1, "code": "unpaid", "description": "Не оплачен"},
#         {"id": 2, "code": "paid", "description": "Оплачен"},
#     ],
#     EventType: [
#         {"id": 1, "code": "pickup", "description": "Забор"},
#         {"id": 2, "code": "delivery", "description": "Доставка"},
#     ],
#     HeaterType: [
#         {"id": 1, "model": "HX-500", "price": 199.99, "weight": 12.5},
#     ],
#     TransportType: [
#         {"id": 1, "name": "van", "avg_speed": 60, "capacity": 1.5},
#     ],
# }


# # ---- helpers -----------------------------------------------------------------
# async def _ensure_ref_data(session: AsyncSession) -> None:
#     """Вставляет данные REF_DATA, если их ещё нет."""
#     for model_cls, rows in REF_DATA.items():
#         present: Sequence[Any] = (await session.scalars(select(model_cls.id))).all()
#         if present:
#             # таблица уже не пуста — пропускаем
#             continue
#         session.add_all(model_cls(**row) for row in rows)
#     await session.flush()


# async def _ensure_admin(session: AsyncSession) -> None:
#     """Создаёт пользователя-админа, если его нет."""
#     settings: Settings = get_settings()
#     admin_email = "root@localhost"
#     admin_pwd = "root"  # в проде передаём через ENV

#     # роль «admin» точно есть после _ensure_ref_data
#     admin_role_id = 1

#     exists: User | None = await session.scalar(select(User).where(User.email == admin_email))
#     if exists:
#         return

#     pwd_hash: str = bcrypt.hash(admin_pwd)
#     admin = User(
#         id=uuid7(),
#         first_name="Root",
#         last_name="User",
#         email=admin_email,
#         phone="+10000000000",
#         avatar_path=None,
#         password_hash=pwd_hash,
#         role_id=admin_role_id,
#     )
#     session.add(admin)
#     typer.echo(f"👑 Admin {admin_email}:{admin_pwd} создан.")


# # ---- main entry --------------------------------------------------------------
# async def init_db() -> None:
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     async with AsyncSessionFactory() as session:
#         await _ensure_ref_data(session)
#         await _ensure_admin(session)
#         await session.commit()

#     typer.echo("✅ База готова и засидирована.")


# @app.command()
# def run() -> None:
#     """Инициализирует БД и заливает дефолтные данные."""
#     asyncio.run(init_db())


# if __name__ == "__main__":
#     app()
