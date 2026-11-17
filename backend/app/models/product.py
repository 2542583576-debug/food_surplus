from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Product(Base):
    """商品：门店当日余量商品（面包/水果/甜品/熟食等）"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="所属商家"
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True, comment="所属分类"
    )
    name: Mapped[str] = mapped_column(String(100), comment="商品名")
    description: Mapped[str] = mapped_column(Text, default="", comment="描述")
    image: Mapped[str] = mapped_column(String(255), default="", comment="主图URL")
    images: Mapped[str] = mapped_column(JSON, default=list, comment="轮播图URL列表(JSON)")
    # 按分类属性模板填写的属性值，如 {"weight": "300g", "filling": "红豆"}
    attributes: Mapped[str] = mapped_column(JSON, default=dict, comment="属性值(JSON，键为模板key)")
    # 当日原价（用于展示"原价 XX 元"），盲盒价在 blind_boxes 表
    original_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, comment="当日原价")
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可售")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    category: Mapped["Category"] = relationship()  # noqa: F821
