from datetime import datetime, time

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BlindBox(Base):
    """盲盒：一组当日余量商品的组合，预约自提"""

    __tablename__ = "blind_boxes"
    __table_args__ = (
        Index("idx_status_pickup", "status", "pickup_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="所属商家"
    )
    title: Mapped[str] = mapped_column(String(100), comment="盲盒标题，如：面包惊喜盒")
    cover_image: Mapped[str] = mapped_column(String(255), default="", comment="封面图")
    # 盲盒内包含的商品及数量，如 [{"product_id":1,"quantity":2},{"product_id":3,"quantity":1}]
    items: Mapped[str] = mapped_column(JSON, default=list, comment="内含商品列表(JSON)")
    description: Mapped[str] = mapped_column(String(500), default="", comment="说明（可能含临期提示等）")
    total_value: Mapped[float] = mapped_column(Numeric(10, 2), default=0, comment="商品总价值(展示用)")
    price: Mapped[float] = mapped_column(Numeric(10, 2), comment="盲盒售价")
    total_stock: Mapped[int] = mapped_column(default=0, comment="总库存/每日投放量")
    sold_count: Mapped[int] = mapped_column(default=0, comment="已售数量")
    # 预约自提时间窗口
    pickup_date: Mapped[datetime] = mapped_column(DateTime, comment="自提日期(当天)")
    pickup_start: Mapped[time] = mapped_column(Time, comment="自提开始时间，如 18:00")
    pickup_end: Mapped[time] = mapped_column(Time, comment="自提截止时间，如 21:00")
    status: Mapped[int] = mapped_column(
        default=0,
        comment="状态：0草稿 1已上架 2已下架 3售罄",
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否推荐位")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
