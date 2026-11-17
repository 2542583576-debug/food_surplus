from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class SurplusBagCreate(BaseModel):
    # 前端表单不带该字段；create 时由后端用登录管理员的门店强制覆盖，update 时不参与修改
    store_id: int | None = None
    bag_name: str
    cover: str | None = None
    description: str | None = None
    original_price: Decimal
    sale_price: Decimal
    stock: int
    pick_start_time: str
    pick_end_time: str
    status: int = 1

class SurplusBagUpdate(SurplusBagCreate):
    pass

class SurplusBagOut(SurplusBagCreate):
    id: int
    create_time: datetime

    class Config:
        from_attributes = True
