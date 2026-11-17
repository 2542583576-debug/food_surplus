"""订单模块测试（SQLite 内存库 + Redis stub）"""
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.session import Base
from app.models import BlindBox, Order, User
from app.schemas.blind_box import BlindBoxCreate
from app.schemas.order import OrderCancelRequest, OrderCreateRequest
from app.schemas.product import ProductCreate
from app.services import blind_box_service as bsvc
from app.services import order_service as osvc
from app.services import product_service as psvc


class FakeRedis:
    """最小 Redis stub：仅实现用到的 incrby/decrby/get/set"""

    def __init__(self):
        self.data = {}

    def set(self, k, v):
        self.data[k] = int(v)

    def get(self, k):
        return self.data.get(k)

    def incrby(self, k, n):
        self.data[k] = self.data.get(k, 0) + n
        return self.data[k]

    def decrby(self, k, n):
        self.data[k] = self.data.get(k, 0) - n
        return self.data[k]


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()
r = FakeRedis()

merchant = User(username="shop1", password_hash="x")
db.add(merchant); db.commit(); db.refresh(merchant)

# 准备分类与商品
from app.models import Category, Product
cat = Category(name="测试")
db.add(cat); db.commit(); db.refresh(cat)
p = Product(merchant_id=merchant.id, category_id=cat.id, name="面包")
db.add(p); db.commit(); db.refresh(p)

box = bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
    title="盒A", price=10.0, total_value=30.0, total_stock=3,
    pickup_date=datetime.now().date() + timedelta(days=1),
    pickup_start=time(18, 0), pickup_end=time(21, 0),
    items=[{"product_id": p.id, "quantity": 1}],
).model_dump())
box = bsvc.change_status(db, merchant.id, box.id, "on_sale", r=r)

# 1. 正常下单：库存 Redis 计数 3 -> 2，DB sold_count=1
o1 = osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000001", quantity=1, customer_name="张三"))
assert r.get("stock:box:%d" % box.id) == 2
assert db.get(BlindBox, box.id).sold_count == 1
assert o1.status == 1 and len(o1.verify_code) == 6 and o1.total_amount == 10.0

# 2. 同人同日重复预约 → 唯一约束拦截，库存回滚
try:
    osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000001", quantity=1))
    raise AssertionError("重复预约应拦截")
except HTTPException as e:
    assert "重复" in e.detail
assert r.get("stock:box:%d" % box.id) == 2  # 回滚后不变

# 3. 抢购到底：库存 3 放 2 单(剩1)后第 3 个不同人可买，第 4 个(需要4个)超卖拦截
o2 = osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000002", quantity=1))
o3 = osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000003", quantity=1))
assert db.get(BlindBox, box.id).sold_count == 3
try:
    osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000004", quantity=1))
    raise AssertionError("超卖应拦截")
except HTTPException as e:
    assert "抢完" in e.detail
assert r.get("stock:box:%d" % box.id) == 0

# 4. 大数量单(2份)在库存0时也拦截
try:
    osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box.id, customer_phone="13800000005", quantity=2))
    raise AssertionError("超卖应拦截")
except HTTPException:
    pass

# 5. 顾客取消：释放库存 3->... 0+1=1? 取消 o1(qty1): DB sold 3->2, redis 0->1
o1 = osvc.cancel_order(db, r, o1.order_no, "13800000001")
assert o1.status == 3
assert db.get(BlindBox, box.id).sold_count == 2
assert r.get("stock:box:%d" % box.id) == 1

# 6. 取消校验：手机号不对 → 404；已完成订单不可取消
try:
    osvc.cancel_order(db, r, o2.order_no, "13999999999")
    raise AssertionError("手机号不匹配应 404")
except HTTPException as e:
    assert e.status_code == 404

# 7. 核销：错误码拒绝，正确码完成
try:
    osvc.verify_order(db, merchant.id, o2.id, "000000")
    raise AssertionError("错误核销码应拒绝")
except HTTPException as e:
    assert "核销码错误" in e.detail
o2 = osvc.verify_order(db, merchant.id, o2.id, o2.verify_code)
assert o2.status == 2 and o2.verified_at is not None
try:
    osvc.verify_order(db, merchant.id, o2.id, o2.verify_code)
    raise AssertionError("已完成订单不可重复核销")
except HTTPException as e:
    assert "待自提" in e.detail

# 8. 过期盲盒不可下单
box_past = bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
    title="昨日盒", price=5.0, total_stock=5,
    pickup_date=datetime.now().date() - timedelta(days=1),
    pickup_start=time(10, 0), pickup_end=time(12, 0),
    items=[{"product_id": p.id, "quantity": 1}],
).model_dump())
bsvc.change_status(db, merchant.id, box_past.id, "on_sale", r=r)
try:
    osvc.create_order(db, r, OrderCreateRequest(blind_box_id=box_past.id, customer_phone="13800000009"))
    raise AssertionError("过期盲盒应拒绝")
except HTTPException as e:
    assert "过期" in e.detail

# 9. 超时未取自动关闭：把 o3 的自提日期改成昨天，跑 release
o3.pickup_date = datetime.now().date() - timedelta(days=1)
db.commit()
count = osvc.release_expired_orders(db, r)
assert count == 1
db.refresh(o3)
assert o3.status == 4
assert db.get(BlindBox, box.id).sold_count == 1  # o3(qty1) 释放: 2->1
assert r.get("stock:box:%d" % box.id) == 2

# 10. 订单列表过滤
total, items = osvc.list_orders(db, merchant.id, 1, 10, status=4)
assert total == 1 and items[0].id == o3.id
total, items = osvc.list_orders(db, merchant.id, 1, 10, keyword="13800000001")
assert total == 1

print("ORDER_MODULE_ALL_TESTS_PASSED")
