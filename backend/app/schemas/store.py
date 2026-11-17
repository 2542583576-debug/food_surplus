"""门店信息 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel


class StoreOut(BaseModel):
    id: int
    store_name: str
    address: str
    phone: str
    cover: str | None = None
    business_hours: str
    longitude: float | None = None
    latitude: float | None = None

    class Config:
        from_attributes = True


class StoreWithBagsOut(StoreOut):
    bag_count: int = 0
