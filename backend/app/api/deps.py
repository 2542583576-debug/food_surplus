"""兼容旧路径的认证依赖，返回轻量 TokenPayload。"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.security import decode_token_payload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


class TokenPayload(BaseModel):
    id: int
    user_id: int
    username: str = ""
    role: int = 0
    store_id: int | None = None

    @property
    def is_merchant(self) -> bool:
        return self.role == 1


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token_payload(token)
    if not payload:
        raise unauthorized
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise unauthorized

    return TokenPayload(
        id=user_id,
        user_id=user_id,
        username=str(payload.get("username", "")),
        role=int(payload.get("role", 0)),
        store_id=payload.get("store_id"),
    )


def require_store_admin(current: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if not current.is_merchant:
        raise HTTPException(status_code=403, detail="仅门店管理员可操作")
    return current


def require_user(current: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if current.is_merchant:
        raise HTTPException(status_code=403, detail="仅普通用户可操作")
    return current
