from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    """下单请求：box_id / bag_id 至少填一个。"""

    box_id: Optional[int] = None
    bag_id: Optional[int] = None
    customer_phone: Optional[str] = None
    customer_name: str = ""
    order_no: Optional[str] = Field(default=None, description="兼容旧接口；留空由服务端生成")
    verify_code: Optional[str] = Field(default=None, description="兼容旧接口；留空由服务端生成")
    pay_amount: Optional[float] = Field(default=None, ge=0, description="留空则取商品售价")
    pay_method: str = Field(default="online", description="online在线支付 store到店付款")
    pickup_date: Optional[date] = None


# 旧接口别名
OrderCreate = OrderCreateRequest


class OrderOut(BaseModel):
    id: int
    order_no: str
    user_id: Optional[int] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    box_id: Optional[int] = None
    bag_id: Optional[int] = None
    store_id: Optional[int] = None
    merchant_id: Optional[int] = None
    verify_code: Optional[str] = None
    pay_amount: float = 0
    pay_method: str = "online"
    pay_status: int = 0
    pickup_date: Optional[date] = None
    status: int
    create_time: Optional[datetime] = None
    verify_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListOut(BaseModel):
    total: int
    items: list[OrderOut]


class OrderVerifyRequest(BaseModel):
    verify_code: str = Field(min_length=4, max_length=20)


class OrderCancelRequest(BaseModel):
    customer_phone: str
