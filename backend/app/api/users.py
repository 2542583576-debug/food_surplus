from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.user import TokenOut, UserLogin, UserRegister, UserOut

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="用户注册")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == user_in.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    role = user_in.role or 0
    if role not in (0, 1):
        raise HTTPException(status_code=400, detail="角色值无效")

    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        phone=user_in.phone,
        nickname=user_in.username,
        role=role,
        store_id=user_in.store_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut, summary="用户登录")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == user_in.username))
    if user is None or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "store_id": user.store_id,
        }
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut, summary="获取当前登录用户信息")
def read_me(
    token_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, token_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
