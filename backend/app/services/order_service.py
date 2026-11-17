"""订单业务逻辑：库存扣减、核销、取消、超时释放、碳记录。"""
import secrets
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import BlindBox, CarbonRecord, Notification, Order, SurplusBag, User
from app.schemas.order import OrderCreateRequest

ORDER_EXPIRE_MINUTES = 15


def _order_no() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(3).upper()


def _verify_code() -> str:
    return str(secrets.randbelow(900000) + 100000)


def create_order(db: Session, r, body: OrderCreateRequest, user_id: int | None = None) -> Order:
    """创建订单，服务端生成订单号/核销码，原子扣减库存。"""
    if not body.box_id and not body.bag_id:
        raise HTTPException(status_code=400, detail="盲盒或魔法袋ID不能为空")

    box = None
    bag = None
    if body.box_id:
        box = db.get(BlindBox, body.box_id)
        if box is None or box.status != 1:
            raise HTTPException(status_code=404, detail="盲盒不存在或已下架")
        if box.sold_count >= box.total_stock:
            raise HTTPException(status_code=400, detail="盲盒已售罄")
        store_id = box.merchant_id
        merchant_id = box.merchant_id
        amount = body.pay_amount if body.pay_amount is not None else float(box.price or 0)
        pickup_date = body.pickup_date
        if pickup_date is None and box.pickup_date:
            pickup_date = box.pickup_date.date() if isinstance(box.pickup_date, datetime) else box.pickup_date
    else:
        bag = db.get(SurplusBag, body.bag_id)
        if bag is None or bag.status != 1:
            raise HTTPException(status_code=404, detail="魔法袋不存在或已下架")
        if bag.stock <= 0:
            raise HTTPException(status_code=400, detail="魔法袋已售罄")
        store_id = bag.store_id
        # 闭环关键：从门店反查所属管理员，让商家端订单列表能看到并核销魔法袋订单
        merchant = (
            db.query(User)
            .filter(User.store_id == bag.store_id, User.role == 1, User.is_active.is_(True))
            .order_by(User.id.asc())
            .first()
        )
        merchant_id = merchant.id if merchant else None
        amount = body.pay_amount if body.pay_amount is not None else float(bag.sale_price or 0)
        pickup_date = body.pickup_date or date.today()

    order = Order(
        order_no=body.order_no or _order_no(),
        user_id=user_id,
        customer_phone=body.customer_phone,
        customer_name=body.customer_name or "",
        box_id=body.box_id,
        bag_id=body.bag_id,
        store_id=store_id,
        merchant_id=merchant_id,
        verify_code=body.verify_code or _verify_code(),
        pay_amount=amount,
        pay_method=body.pay_method or "online",
        pay_status=0,  # 待支付
        pickup_date=pickup_date,
        status=1,  # 待自提
        expire_time=datetime.now() + timedelta(minutes=ORDER_EXPIRE_MINUTES),
        create_time=datetime.now(),
    )
    try:
        if box is not None:
            box.sold_count += 1
        if bag is not None:
            bag.stock -= 1
        db.add(order)
        db.flush()
        # 下单成功通知（登录用户）
        if user_id:
            db.add(Notification(
                user_id=user_id,
                title="预订成功",
                content="你的余量魔法袋已预订成功，请按领取时段到店出示核销码。",
                type="success",
                order_id=order.id,
            ))
        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise
    return order


def cancel_order(db: Session, r, order_no: str, customer_phone: str) -> Order:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 1:
        raise HTTPException(status_code=400, detail="当前订单状态不支持取消")
    if customer_phone and order.customer_phone != customer_phone:
        raise HTTPException(status_code=403, detail="手机号与订单不匹配")

    _restore_stock(db, order)
    order.status = 3  # 已取消
    db.commit()
    db.refresh(order)
    return order


def list_orders(
    db: Session,
    merchant_id: int,
    page: int,
    size: int,
    status: int | None,
    pickup_date: date | None,
    keyword: str | None,
) -> tuple[int, list[Order]]:
    q = db.query(Order).filter(Order.merchant_id == merchant_id)
    if status is not None:
        q = q.filter(Order.status == status)
    if pickup_date is not None:
        q = q.filter(Order.pickup_date == pickup_date)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            or_(Order.customer_phone.like(kw), Order.order_no.like(kw), Order.customer_name.like(kw))
        )
    total = q.count()
    items = q.order_by(Order.create_time.desc()).offset((page - 1) * size).limit(size).all()
    return total, items


def verify_order(
    db: Session,
    merchant_id: int,
    order_id: int,
    verify_code: str,
    store_id: int | None = None,
) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if store_id is not None:
        if order.store_id and order.store_id != store_id:
            raise HTTPException(status_code=403, detail="只能核销本店订单")
    elif order.merchant_id != merchant_id:
        raise HTTPException(status_code=403, detail="只能核销本店订单")
    if order.status != 1:
        raise HTTPException(status_code=400, detail="订单状态不支持核销")
    if order.verify_code != verify_code:
        raise HTTPException(status_code=400, detail="核销码错误")

    order.status = 2  # 已完成
    order.verify_time = datetime.now()
    order.pay_status = 1  # 核销即完成支付

    # 核销成功通知
    if order.user_id:
        db.add(Notification(
            user_id=order.user_id,
            title="核销成功",
            content="你已成功领取魔法袋，减少食物浪费的碳减排记录已计入你的环保账本。",
            type="success",
            order_id=order.id,
        ))

    # 生成碳减排记录：按每个魔法袋/盲盒约 0.5kg 食物、1.2kg 碳估算
    carbon = CarbonRecord(
        order_id=order.id,
        bag_id=order.bag_id or 0,
        store_id=order.store_id or 0,
        user_id=order.user_id or 0,
        save_food_weight=0.5,
        reduce_carbon=1.2,
        create_time=datetime.now(),
    )
    db.add(carbon)
    db.commit()
    db.refresh(order)
    return order


def _restore_stock(db: Session, order: Order) -> None:
    if order.box_id:
        box = db.get(BlindBox, order.box_id)
        if box and box.sold_count > 0:
            box.sold_count -= 1
    if order.bag_id:
        bag = db.get(SurplusBag, order.bag_id)
        if bag:
            bag.stock += 1


def init_box_stock(r, box) -> None:
    """盲盒上架时初始化缓存库存计数（Redis 不可用时静默跳过）。"""
    if r is None:
        return
    try:
        r.set(f"box:stock:{box.id}", max(0, box.total_stock - box.sold_count))
    except Exception:
        pass


def release_expired_orders(db: Session) -> int:
    """超时订单自动释放库存（供启动后台任务调用）。"""
    expired = db.query(Order).filter(
        Order.status == 1,
        Order.expire_time.isnot(None),
        Order.expire_time < datetime.now(),
    ).all()
    for order in expired:
        _restore_stock(db, order)
        order.status = 4  # 超时
    if expired:
        db.commit()
    return len(expired)
