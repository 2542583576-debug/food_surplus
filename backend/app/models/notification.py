"""站内通知：下单成功、核销成功等消息提醒。"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.db.session import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="通知ID")
    user_id = Column(Integer, nullable=False, index=True, comment="接收用户ID")
    title = Column(String(100), nullable=False, comment="标题")
    content = Column(String(255), default="", comment="内容")
    type = Column(String(20), default="info", comment="类型：success/info/warning")
    order_id = Column(Integer, nullable=True, comment="关联订单ID")
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
