from sqlalchemy import Column, Integer, DECIMAL, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class CarbonRecord(Base):
    __tablename__ = "carbon_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="记录ID")
    order_id = Column(Integer, nullable=False, comment="关联订单ID")
    bag_id = Column(Integer, nullable=False, comment="余量魔法袋ID")
    store_id = Column(Integer, nullable=False, comment="门店ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    save_food_weight = Column(DECIMAL(10,2), nullable=False, comment="节约食物重量(kg)")
    reduce_carbon = Column(DECIMAL(10,2), nullable=False, comment="减少碳排放(kg)")
    create_time = Column(DateTime, default=func.now(), comment="记录生成时间")
