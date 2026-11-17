from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.db.session import Base


class Order(Base):
    """订单：兼容顾客预约（盲盒）与余量魔法袋下单两种业务。"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="订单ID")
    order_no = Column(String(64), unique=True, nullable=False, index=True, comment="订单号")
    user_id = Column(Integer, nullable=True, index=True, comment="下单用户ID（登录时）")
    customer_phone = Column(String(20), nullable=True, index=True, comment="顾客手机号")
    customer_name = Column(String(50), default="", comment="顾客称呼")
    box_id = Column(Integer, nullable=True, index=True, comment="关联盲盒ID")
    bag_id = Column(Integer, nullable=True, index=True, comment="关联魔法袋ID")
    store_id = Column(Integer, nullable=True, index=True, comment="门店ID")
    merchant_id = Column(Integer, nullable=True, index=True, comment="商家ID")
    verify_code = Column(String(20), nullable=True, index=True, comment="核销码")
    pay_amount = Column(Numeric(10, 2), default=0, comment="实付金额")
    pay_method = Column(String(20), default="online", comment="支付方式：online在线支付 store到店付款")
    pay_status = Column(Integer, default=0, nullable=False, index=True, comment="支付状态：0待支付 1已支付 2已退款")
    pickup_date = Column(Date, nullable=True, index=True, comment="预约自提日期")
    # 1待自提 2已完成 3已取消 4超时/过期
    status = Column(Integer, default=1, nullable=False, index=True, comment="订单状态")
    expire_time = Column(DateTime, nullable=True, comment="订单过期时间")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    verify_time = Column(DateTime, nullable=True, comment="核销时间")

    # 兼容管理端页面使用的字段名
    @property
    def quantity(self) -> int:
        return 1

    @property
    def total_amount(self) -> float:
        return float(self.pay_amount or 0)

    @property
    def created_at(self):
        return self.create_time
