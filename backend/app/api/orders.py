from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_store_admin
from app.db.session import get_db
from app.models import Order, SurplusBag
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import create_order as create_order_svc, verify_order as verify_order_svc

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="用户下单")
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not order_in.bag_id:
        raise HTTPException(status_code=400, detail="请指定魔法袋")
    return create_order_svc(db, None, order_in, user_id=current_user.id)


@router.get("/", response_model=list[OrderOut], summary="查询我的订单列表")
def list_order(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.create_time.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderOut, summary="订单详情")
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.put("/{order_id}/verify", response_model=OrderOut, summary="门店核销订单")
def verify_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_store_admin),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.store_id and current_user.store_id and order.store_id != current_user.store_id:
        raise HTTPException(status_code=403, detail="只能核销本店订单")
    return verify_order_svc(
        db,
        merchant_id=order.merchant_id or 0,
        order_id=order_id,
        verify_code=order.verify_code,
        store_id=current_user.store_id,
    )
