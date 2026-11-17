from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator


class BlindBoxItem(BaseModel):
    """盲盒内单个商品"""
    product_id: int
    quantity: int = Field(ge=1, le=99)


class BlindBoxCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    cover_image: str = ""
    items: list[BlindBoxItem] = Field(min_length=1)
    description: str = Field(default="", max_length=500)
    price: float = Field(gt=0, le=99999)
    total_value: float = Field(default=0, ge=0)
    total_stock: int = Field(ge=1, le=9999)
    pickup_date: datetime
    pickup_start: time
    pickup_end: time
    is_featured: bool = False

    @model_validator(mode="after")
    def check_pickup_window(self):
        if self.pickup_start >= self.pickup_end:
            raise ValueError("自提开始时间必须早于截止时间")
        return self


class BlindBoxUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    cover_image: str | None = None
    items: list[BlindBoxItem] | None = None
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0, le=99999)
    total_value: float | None = Field(default=None, ge=0)
    total_stock: int | None = Field(default=None, ge=1, le=9999)
    pickup_date: datetime | None = None
    pickup_start: time | None = None
    pickup_end: time | None = None
    is_featured: bool | None = None

    @model_validator(mode="after")
    def check_pickup_window(self):
        start = self.pickup_start
        end = self.pickup_end
        if start is not None and end is not None and start >= end:
            raise ValueError("自提开始时间必须早于截止时间")
        return self


STATUS_DRAFT = 0
STATUS_ON_SALE = 1
STATUS_OFF_SALE = 2
STATUS_SOLD_OUT = 3
STATUS_MAP = {STATUS_DRAFT: "草稿", STATUS_ON_SALE: "已上架", STATUS_OFF_SALE: "已下架", STATUS_SOLD_OUT: "售罄"}


class BlindBoxStatusRequest(BaseModel):
    action: str = Field(pattern=r"^(on_sale|off_sale)$")  # 上架/下架


class BlindBoxOut(BaseModel):
    id: int
    merchant_id: int
    title: str
    cover_image: str
    items: list[dict]
    description: str
    total_value: float
    price: float
    total_stock: int
    sold_count: int
    pickup_date: datetime
    pickup_start: time
    pickup_end: time
    status: int
    is_featured: bool

    class Config:
        from_attributes = True


class BlindBoxListOut(BaseModel):
    total: int
    items: list[BlindBoxOut]
