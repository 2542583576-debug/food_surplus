"""统一密码哈希与 JWT 工具。

同时兼容两套历史调用方式：
- hash_password / get_password_hash
- create_access_token(user_id:int) 与 create_access_token(data:dict)
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt 仅支持 72 字节以内密码，超长输入先截断，避免 500
MAX_PASSWORD_BYTES = 72


def _clip(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) <= MAX_PASSWORD_BYTES:
        return password
    return raw[:MAX_PASSWORD_BYTES].decode("utf-8", errors="ignore")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(_clip(plain_password))


def get_password_hash(plain_password: str) -> str:
    """旧接口别名"""
    return hash_password(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(_clip(plain_password), hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(subject, expires_delta: timedelta | None = None) -> str:
    """subject 可以是用户 ID(int) 或自定义 payload(dict)。"""
    if isinstance(subject, dict):
        payload = subject.copy()
    else:
        payload = {"sub": str(subject)}

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """解析 token 并返回用户 ID，失败返回 None。"""
    payload = decode_token_payload(token)
    if not payload:
        return None
    sub = payload.get("sub")
    try:
        return int(sub)
    except (TypeError, ValueError):
        return None


def decode_token_payload(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None
