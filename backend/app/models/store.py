from sqlalchemy import Column, Integer, String, DateTime, Float, func
from sqlalchemy.dialects.mysql import TINYINT as TinyInteger
from app.db.session import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    store_name = Column(String(100), nullable=False, comment="门店名称")
    address = Column(String(255), nullable=False, comment="门店地址")
    phone = Column(String(20), nullable=False, comment="联系电话")
    cover = Column(String(255), nullable=True, comment="封面图")
    business_hours = Column(String(100), nullable=False, comment="营业时间")
    longitude = Column(Float, nullable=True, comment="经度")
    latitude = Column(Float, nullable=True, comment="纬度")
    status = Column(TinyInteger, default=1, comment="1启用 0停用")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
