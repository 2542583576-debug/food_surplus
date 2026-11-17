"""商品 + 盲盒模块测试（SQLite 内存库）"""
from datetime import date, time, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.session import Base
from app.models import BlindBox, Product, User
from app.schemas.blind_box import BlindBoxCreate, BlindBoxUpdate
from app.schemas.category import AttributeField, AttributeTemplateCreate, CategoryCreate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import blind_box_service as bsvc
from app.services import category_service as csvc
from app.services import product_service as psvc

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

merchant = User(username="shop1", password_hash="x", shop_name="测试面包房")
db.add(merchant)
db.commit()
db.refresh(merchant)

# 准备分类 + 属性模板
bread = csvc.create_category(db, CategoryCreate(name="面包"))
tpl = csvc.create_template(db, AttributeTemplateCreate(
    category_id=bread.id, name="面包属性",
    fields=[
        AttributeField(key="weight", label="克重", type="number", required=True),
        AttributeField(key="filling", label="馅料", type="select", options=["红豆", "奶黄", "无"]),
    ],
))

# 1. 属性校验：缺必填 → 拒绝
try:
    psvc.create_product(db, merchant.id, ProductCreate(category_id=bread.id, name="吐司", attributes={"filling": "无"}).model_dump())
    raise AssertionError("缺必填属性应拒绝")
except Exception as e:
    assert "必填" in str(getattr(e, "detail", str(e)))

# 2. 属性校验：select 值非法 → 拒绝
try:
    psvc.create_product(db, merchant.id, ProductCreate(category_id=bread.id, name="吐司", attributes={"weight": 300, "filling": "榴莲"}).model_dump())
    raise AssertionError("非法选项应拒绝")
except Exception as e:
    assert "不在可选项" in str(getattr(e, "detail", str(e)))

# 3. 正常创建
p1 = psvc.create_product(db, merchant.id, ProductCreate(category_id=bread.id, name="红豆吐司", original_price=15.5, attributes={"weight": 300, "filling": "红豆"}).model_dump())
assert p1.original_price == 15.5 and p1.attributes["filling"] == "红豆"

# 4. 更新商品属性（合法）
p1 = psvc.update_product(db, merchant.id, p1.id, ProductUpdate(attributes={"weight": 350, "filling": "奶黄"}).model_dump(exclude_unset=True))
assert p1.attributes["filling"] == "奶黄"

# 5. 换分类但属性不合法 → 拒绝
fruit = csvc.create_category(db, CategoryCreate(name="水果"))
csvc.create_template(db, AttributeTemplateCreate(category_id=fruit.id, name="水果属性", fields=[AttributeField(key="origin", label="产地", type="text", required=True)]))
try:
    psvc.update_product(db, merchant.id, p1.id, ProductUpdate(category_id=fruit.id).model_dump(exclude_unset=True))
    raise AssertionError("换分类后缺新必填属性应拒绝")
except Exception as e:
    assert "必填" in str(getattr(e, "detail", str(e)))

# 6. 商品隔离：第二个商家的商品，商家1查不到
m2 = User(username="shop2", password_hash="x")
db.add(m2); db.commit(); db.refresh(m2)
try:
    psvc.get_product_or_404(db, p1.id, m2.id)
    raise AssertionError("跨商家访问应 404")
except Exception as e:
    assert "不存在" in str(getattr(e, "detail", str(e)))

# 7. 盲盒：引用别人的商品 → 拒绝
p_other = psvc.create_product(db, m2.id, ProductCreate(category_id=bread.id, name="别家的", attributes={"weight": 1}).model_dump())
try:
    bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
        title="盒1", price=9.9, total_stock=10,
        pickup_date=datetime(2026, 11, 17), pickup_start=time(18, 0), pickup_end=time(21, 0),
        items=[{"product_id": p_other.id, "quantity": 1}],
    ).model_dump())
    raise AssertionError("引用他人商品应拒绝")
except Exception as e:
    assert "不属于当前商家" in str(getattr(e, "detail", str(e)))

# 8. 自提时间窗口校验
try:
    bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
        title="盒2", price=9.9, total_stock=10,
        pickup_date=datetime(2026, 11, 17), pickup_start=time(21, 0), pickup_end=time(18, 0),
        items=[{"product_id": p1.id, "quantity": 2}],
    ).model_dump())
    raise AssertionError("自提时间倒挂应拒绝")
except ValueError:
    pass  # pydantic model_validator 拦截

# 9. 正常建盲盒（草稿）→ 上架 → 上架状态不可编辑 → 下架 → 可编辑/可删
box = bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
    title="面包惊喜盒", price=9.9, total_value=28.0, total_stock=20,
    pickup_date=datetime(2026, 11, 17), pickup_start=time(18, 0), pickup_end=time(21, 0),
    items=[{"product_id": p1.id, "quantity": 2}],
).model_dump())
assert box.status == 0

box = bsvc.change_status(db, merchant.id, box.id, "on_sale")
assert box.status == 1

try:
    bsvc.update_blind_box(db, merchant.id, box.id, BlindBoxUpdate(title="改名").model_dump(exclude_unset=True))
    raise AssertionError("上架中不可编辑")
except Exception as e:
    assert "先下架" in str(getattr(e, "detail", str(e)))

box = bsvc.change_status(db, merchant.id, box.id, "off_sale")
assert box.status == 2
box = bsvc.update_blind_box(db, merchant.id, box.id, BlindBoxUpdate(title="面包惊喜盒v2").model_dump(exclude_unset=True))
assert box.title == "面包惊喜盒v2"
bsvc.delete_blind_box(db, merchant.id, box.id)
assert db.get(BlindBox, box.id) is None

# 10. 状态流转：草稿不能直接下架
box2 = bsvc.create_blind_box(db, merchant.id, BlindBoxCreate(
    title="盒3", price=5.0, total_stock=5,
    pickup_date=datetime(2026, 11, 18), pickup_start=time(10, 0), pickup_end=time(12, 0),
    items=[{"product_id": p1.id, "quantity": 1}],
).model_dump())
try:
    bsvc.change_status(db, merchant.id, box2.id, "off_sale")
    raise AssertionError("草稿不可下架")
except Exception as e:
    assert "仅已上架" in str(getattr(e, "detail", str(e)))

# 11. 列表分页
total, items = bsvc.list_blind_boxes(db, merchant.id, page=1, size=10)
assert total == 1 and items[0].title == "盒3"
total, items = psvc.list_products(db, merchant.id, page=1, size=10, keyword="红豆")
assert total == 1 and items[0].name == "红豆吐司"

print("PRODUCT_BLINDBOX_ALL_TESTS_PASSED")
