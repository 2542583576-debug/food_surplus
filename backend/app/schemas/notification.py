"""通知相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    title: str
    content: str = ""
    type: str = "info"
    order_id: int | None = None
    is_read: bool = False
    create_time: datetime | None = None

    class Config:
        from_attributes = True


class UnreadCountOut(BaseModel):
    unread: int
