import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BlindBox, Product, User
from app.schemas.blind_box import STATUS_DRAFT, STATUS_OFF_SALE, STATUS_ON_SALE


def _validate_items(db: Session, merchant_id: int, items: list[dict]) -> None:
    """校验盲盒内商品：存在、属于当前商家"""
    product_ids = {i["product_id"] for i in items}
    products = db.scalars(
        select(Product).where(Product.id.in_(product_ids), Product.merchant_id == merchant_id)
    ).all()
    found_ids = {p.id for p in products}
    missing = product_ids - found_ids
    if missing:
        raise HTTPException(status_code=400, detail=f"商品不存在或不属于当前商家: {sorted(missing)}")


def get_box_or_404(db: Session, box_id: int, merchant_id: int) -> BlindBox:
    obj = db.get(BlindBox, box_id)
    if obj is None or obj.merchant_id != merchant_id:
        raise HTTPException(status_code=404, detail="盲盒不存在")
    return obj


def create_blind_box(db: Session, merchant_id: int, data: dict) -> BlindBox:
    _validate_items(db, merchant_id, data["items"])
    obj = BlindBox(merchant_id=merchant_id, status=STATUS_DRAFT, **data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_blind_box(db: Session, merchant_id: int, box_id: int, data: dict) -> BlindBox:
    obj = get_box_or_404(db, box_id, merchant_id)
    if obj.status == STATUS_ON_SALE:
        raise HTTPException(status_code=400, detail="已上架的盲盒不可编辑，请先下架")
    if "items" in data:
        _validate_items(db, merchant_id, data["items"])
    # 校验自提时间窗口（可能单独更新 start 或 end）
    start = data.get("pickup_start", obj.pickup_start)
    end = data.get("pickup_end", obj.pickup_end)
    if start >= end:
        raise HTTPException(status_code=400, detail="自提开始时间必须早于截止时间")
    for field, value in data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def change_status(db: Session, merchant_id: int, box_id: int, action: str, r=None) -> BlindBox:
    obj = get_box_or_404(db, box_id, merchant_id)
    if action == "on_sale":
        if obj.status not in (STATUS_DRAFT, STATUS_OFF_SALE):
            raise HTTPException(status_code=400, detail="当前状态不允许上架")
        if obj.sold_count >= obj.total_stock:
            raise HTTPException(status_code=400, detail="库存不足，无法上架")
        obj.status = STATUS_ON_SALE
        if r is not None:
            from app.services.order_service import init_box_stock
            init_box_stock(r, obj)  # 上架时初始化 Redis 库存计数
    else:  # off_sale
        if obj.status != STATUS_ON_SALE:
            raise HTTPException(status_code=400, detail="仅已上架的盲盒可以下架")
        obj.status = STATUS_OFF_SALE
    db.commit()
    db.refresh(obj)
    return obj


def delete_blind_box(db: Session, merchant_id: int, box_id: int) -> None:
    obj = get_box_or_404(db, box_id, merchant_id)
    if obj.status == STATUS_ON_SALE:
        raise HTTPException(status_code=400, detail="已上架的盲盒不可删除，请先下架")
    db.delete(obj)
    db.commit()


def list_blind_boxes(
    db: Session, merchant_id: int, page: int, size: int,
    status: int | None = None, pickup_date: datetime | None = None,
) -> tuple[int, list[BlindBox]]:
    stmt = select(BlindBox).where(BlindBox.merchant_id == merchant_id)
    if status is not None:
        stmt = stmt.where(BlindBox.status == status)
    if pickup_date is not None:
        stmt = stmt.where(func.date(BlindBox.pickup_date) == pickup_date.date())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(BlindBox.id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return total, list(items)
