from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from decimal import Decimal

from app.db.session import get_db
from app.models.carbon_record import CarbonRecord
from app.schemas.carbon_record import CarbonRecordOut, CarbonSummaryOut

router = APIRouter(prefix="/api/carbon", tags=["碳减排统计"])

# 用户个人节约记录列表
@router.get("/user/records", response_model=List[CarbonRecordOut])
def get_user_carbon_records(
    user_id: int,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db)
):
    q = db.query(CarbonRecord).filter(CarbonRecord.user_id == user_id).order_by(CarbonRecord.create_time.desc())
    return q.offset((page - 1) * size).limit(size).all()

# 用户个人汇总数据
@router.get("/user/summary", response_model=CarbonSummaryOut)
def get_user_carbon_summary(user_id: int, db: Session = Depends(get_db)):
    res = db.query(
        func.sum(CarbonRecord.save_food_weight).label("total_save_food"),
        func.sum(CarbonRecord.reduce_carbon).label("total_reduce_carbon"),
        func.count(CarbonRecord.id).label("total_order_count")
    ).filter(CarbonRecord.user_id == user_id).first()
    return CarbonSummaryOut(
        total_save_food=res.total_save_food or Decimal(0),
        total_reduce_carbon=res.total_reduce_carbon or Decimal(0),
        total_order_count=res.total_order_count or 0
    )

# 门店汇总数据
@router.get("/store/summary", response_model=CarbonSummaryOut)
def get_store_carbon_summary(store_id: int, db: Session = Depends(get_db)):
    res = db.query(
        func.sum(CarbonRecord.save_food_weight).label("total_save_food"),
        func.sum(CarbonRecord.reduce_carbon).label("total_reduce_carbon"),
        func.count(CarbonRecord.id).label("total_order_count")
    ).filter(CarbonRecord.store_id == store_id).first()
    return CarbonSummaryOut(
        total_save_food=res.total_save_food or Decimal(0),
        total_reduce_carbon=res.total_reduce_carbon or Decimal(0),
        total_order_count=res.total_order_count or 0
    )

# 平台全局汇总
@router.get("/platform/summary", response_model=CarbonSummaryOut)
def get_platform_carbon_summary(db: Session = Depends(get_db)):
    res = db.query(
        func.sum(CarbonRecord.save_food_weight).label("total_save_food"),
        func.sum(CarbonRecord.reduce_carbon).label("total_reduce_carbon"),
        func.count(CarbonRecord.id).label("total_order_count")
    ).first()
    return CarbonSummaryOut(
        total_save_food=res.total_save_food or Decimal(0),
        total_reduce_carbon=res.total_reduce_carbon or Decimal(0),
        total_order_count=res.total_order_count or 0
    )
