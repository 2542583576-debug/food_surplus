from typing import Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    phone: Optional[str] = None
    role: int = 0  # 0普通用户 1门店管理员
    store_id: Optional[int] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    role: int = 0
    store_id: Optional[int] = None
    nickname: Optional[str] = None
    shop_name: Optional[str] = None

    class Config:
        from_attributes = True
