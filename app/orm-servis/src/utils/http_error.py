# src/utils/http_error.py
from typing import NoReturn

from fastapi import HTTPException


def _raise_400(exc: ValueError) -> NoReturn:
    raise HTTPException(status_code=400, detail=str(exc)) from exc

def _raise_401(message: str = "Неавторизован") -> NoReturn:
    raise HTTPException(status_code=401, detail=message)

def _raise_404(message: str = "Не найдено") -> NoReturn:
    raise HTTPException(status_code=404, detail=message)


def _raise_409(message: str = "Конфликт данных") -> NoReturn:
    raise HTTPException(status_code=409, detail=message)


def _raise_422(message: str = "Невалидные данные") -> NoReturn:
    raise HTTPException(status_code=422, detail=message)


def _raise_500(message: str = "Внутренняя ошибка сервера") -> NoReturn:
    raise HTTPException(status_code=500, detail=message)
