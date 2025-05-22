# from datetime import datetime

# from pydantic import BaseModel, ConfigDict, EmailStr


# class _UserBase(BaseModel):
#     email: EmailStr
#     full_name: str | None = None

#     model_config = ConfigDict(from_attributes=True)


# class UserCreate(_UserBase):
#     password: str


# class UserRead(_UserBase):
#     id: int
#     created_at: datetime
