from typing import Any

from sqlalchemy import Function, func

from src.db.models import Address, User


def location_expr() -> Function[Any]:
    """Подзапрос объединения адреса без label — используешь где хочешь."""
    return func.concat_ws(
        ", ",
        func.coalesce(Address.city, ""),
        func.coalesce(Address.street, ""),
        func.coalesce(Address.building, ""),
    )


def full_name_expr() -> Function[Any]:
    """Имя Фамилия user"""
    return func.concat_ws(
        " ",
        func.coalesce(User.first_name, ""),
        func.coalesce(User.last_name, ""),
    )
