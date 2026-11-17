from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class CarbonRecordOut(BaseModel):
    id: int
    order_id: int
    bag_id: int
    store_id: int
    user_id: int
    save_food_weight: Decimal
    reduce_carbon: Decimal
    create_time: datetime

    class Config:
        from_attributes = True

# 汇总统计返回
class CarbonSummaryOut(BaseModel):
    total_save_food: Decimal
    total_reduce_carbon: Decimal
    total_order_count: int
