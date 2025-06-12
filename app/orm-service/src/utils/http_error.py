# src/utils/http_error.py
from fastapi import HTTPException


class APIException(HTTPException):
    status_code: int = 400
    detail: str = "Ошибка запроса"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(status_code=self.status_code, detail=detail or self.detail)


class BadRequestError(APIException):
    status_code = 400
    detail = "Некорректный запрос"


class UnauthorizedError(APIException):
    status_code = 401
    detail = "Неавторизован"


class NotFoundError(APIException):
    status_code = 404
    detail = "Не найдено"


class ConflictError(APIException):
    status_code = 409
    detail = "Конфликт данных"


class UnprocessableEntityError(APIException):
    status_code = 422
    detail = "Невалидные данные"


class InternalServerError(APIException):
    status_code = 500
    detail = "Внутренняя ошибка сервера"
