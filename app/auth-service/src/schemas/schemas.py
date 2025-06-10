# src/schemas/schemas.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SerializationInfo, field_serializer

from src.db.models import Role


# ─────────────────────────── Auth ────────────────────────────
class AuthLogin(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: UUID
    role: str
    exp: int


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str | None = None
    phone: str
    avatar_path: str | None = None

    role: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("role")
    def _serialize_role(self, v: Role | str, info: SerializationInfo) -> str:
        return v.name if isinstance(v, Role) else v
