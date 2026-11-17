from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    image: str = ""
    images: list[str] = []
    attributes: dict[str, object] = {}  # 键为分类模板中的属性 key
    original_price: float = Field(default=0, ge=0, le=99999)
    is_on_sale: bool = True


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    image: str | None = None
    images: list[str] | None = None
    attributes: dict[str, object] | None = None
    original_price: float | None = Field(default=None, ge=0, le=99999)
    is_on_sale: bool | None = None


class ProductOut(BaseModel):
    id: int
    merchant_id: int
    category_id: int
    name: str
    description: str
    image: str
    images: list[str]
    attributes: dict[str, object]
    original_price: float
    is_on_sale: bool

    class Config:
        from_attributes = True


class ProductListOut(BaseModel):
    """列表页：不带大字段，分页用"""
    total: int
    items: list[ProductOut]
