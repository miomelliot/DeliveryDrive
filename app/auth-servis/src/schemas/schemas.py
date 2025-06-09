from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


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
