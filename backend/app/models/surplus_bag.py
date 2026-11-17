from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.db.session import Base

class SurplusBag(Base):
    __tablename__ = "surplus_bags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="魔法袋ID")
    store_id = Column(Integer, nullable=False, comment="所属门店id，关联stores")
    bag_name = Column(String(100), nullable=False, comment="余量魔法袋名称")
    cover = Column(String(255), nullable=True, comment="魔法袋封面图")
    description = Column(Text, nullable=True, comment="内容说明，例如面包、甜品余量")
    original_price = Column(DECIMAL(10,2), nullable=False, comment="原价")
    sale_price = Column(DECIMAL(10,2), nullable=False, comment="售卖价")
    stock = Column(Integer, default=0, comment="当日剩余库存")
    pick_start_time = Column(String(50), nullable=False, comment="最早领取时间")
    pick_end_time = Column(String(50), nullable=False, comment="最晚领取时间")
    status = Column(Integer, default=1, comment="1上架 0下架")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
