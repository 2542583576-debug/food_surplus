from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.redis import get_redis
from app.db.session import get_db
from app.models import User
from app.schemas.order import OrderCancelRequest, OrderCreateRequest, OrderListOut, OrderOut, OrderVerifyRequest
from app.services import order_service as svc

# C 端接口（无需登录，手机号即身份）：/api/v1/orders/*
customer_router = APIRouter(prefix="/orders", tags=["订单-C端"])


@customer_router.post("/create", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="顾客预约下单")
def create_order(body: OrderCreateRequest, db: Session = Depends(get_db), r=Depends(get_redis)):
    return svc.create_order(db, r, body)


@customer_router.post("/{order_no}/cancel", response_model=OrderOut, summary="顾客取消订单")
def cancel_order(order_no: str, body: OrderCancelRequest, db: Session = Depends(get_db), r=Depends(get_redis)):
    return svc.cancel_order(db, r, order_no, body.customer_phone)


# 商家接口（需登录）：/api/v1/merchant/orders/*
merchant_router = APIRouter(
    prefix="/merchant/orders",
    dependencies=[Depends(get_current_user)],
    tags=["订单-商家"],
)


@merchant_router.get("", response_model=OrderListOut, summary="订单列表(分页)")
def list_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    status: int | None = Query(default=None, description="1待自提 2已完成 3已取消 4超时"),
    pickup_date: date | None = None,
    keyword: str | None = Query(default=None, description="手机号/订单号/姓名"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, items = svc.list_orders(db, current_user.id, page, size, status, pickup_date, keyword)
    return OrderListOut(total=total, items=items)


@merchant_router.post("/{order_id}/verify", response_model=OrderOut, summary="核销订单(到店自提)")
def verify_order(
    order_id: int,
    body: OrderVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.verify_order(db, current_user.id, order_id, body.verify_code)
