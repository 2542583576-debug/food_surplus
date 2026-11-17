from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """用户：普通顾客(role=0) 与门店管理员(role=1) 共用一张表。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 密码哈希")
    nickname = Column(String(50), default="", comment="昵称")
    shop_name = Column(String(100), default="", comment="门店名称（管理员）")
    phone = Column(String(20), unique=True, nullable=True, index=True, comment="手机号")
    role = Column(Integer, default=0, nullable=False, comment="0普通用户 1门店管理员")
    store_id = Column(Integer, nullable=True, comment="绑定门店ID")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

    @property
    def is_merchant(self) -> bool:
        return self.role == 1
