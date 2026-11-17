from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="登录名")
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=50)
    shop_name: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20, pattern=r"^1[3-9]\d{9}$|^$")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    shop_name: Optional[str] = None
    phone: Optional[str] = None
    role: int = 0

    class Config:
        from_attributes = True
