from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Для запроса ---
class AuthRequest(BaseModel):
    email: EmailStr
    password: str


# --- Для успешного ответа (JWT) ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: UUID = Field(..., description="User UUID")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")


# --- Для возврата данных пользователя (например, /me) ---
class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str | None = None
    phone: str
    avatar_path: str | None = None
    role: str

    class Config:
        orm_mode = True
