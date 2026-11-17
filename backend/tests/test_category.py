"""临时验证脚本：SQLite 内存库测试分类模块（验证后可删）"""
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.session import Base
from app.models import User
from app.schemas.category import AttributeField, AttributeTemplateCreate, CategoryCreate, CategoryMoveRequest
from app.services import category_service as svc

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

# 建分类树: 食品(根) -> 面包/水果; 面包 -> 欧包
food = svc.create_category(db, CategoryCreate(name="食品"))
bread = svc.create_category(db, CategoryCreate(name="面包", parent_id=food.id))
svc.create_category(db, CategoryCreate(name="水果", parent_id=food.id, sort_order=2))
eu = svc.create_category(db, CategoryCreate(name="欧包", parent_id=bread.id))

# 树构建
tree = svc.get_category_tree(db)
assert len(tree) == 1 and tree[0]["name"] == "食品"
assert {c["name"] for c in tree[0]["children"]} == {"面包", "水果"}
assert tree[0]["children"][0]["children"][0]["name"] == "欧包"

# 循环引用拦截：把"食品"移到"欧包"下（欧包是食品的子孙）
try:
    svc.move_category(db, food.id, CategoryMoveRequest(parent_id=eu.id))
    raise AssertionError("应当拦截循环引用")
except Exception as e:
    assert "子孙" in str(getattr(e, "detail", str(e)))

# 自引用拦截
try:
    svc.move_category(db, food.id, CategoryMoveRequest(parent_id=food.id))
    raise AssertionError("应当拦截自引用")
except Exception as e:
    assert "自己" in str(getattr(e, "detail", str(e)))

# 有子分类时禁止删除
try:
    svc.delete_category(db, bread.id)
    raise AssertionError("应当拦截有子分类的删除")
except Exception as e:
    assert "子分类" in str(getattr(e, "detail", str(e)))

# 属性模板 CRUD
tpl = svc.create_template(db, AttributeTemplateCreate(
    category_id=bread.id, name="面包基础属性",
    fields=[
        AttributeField(key="weight", label="克重", type="number", required=True),
        AttributeField(key="filling", label="馅料", type="select", options=["红豆", "奶黄", "无"]),
    ],
))
out = svc.template_to_dict(tpl)
assert out["fields"][0]["key"] == "weight" and out["fields"][1]["options"] == ["红豆", "奶黄", "无"]

# 更新模板
tpl2 = svc.update_template(db, tpl.id, __import__("app.schemas.category", fromlist=["AttributeTemplateUpdate"]).AttributeTemplateUpdate(name="面包属性v2"))
assert svc.template_to_dict(tpl2)["name"] == "面包属性v2"

# 删除叶子分类 OK，模板级联删除
svc.delete_category(db, eu.id)
assert db.get(__import__("app.models", fromlist=["Category"]).Category, eu.id) is None

# 面包是叶子了，删除应成功并级联删模板
svc.delete_category(db, bread.id)
assert db.query(__import__("app.models", fromlist=["AttributeTemplate"]).AttributeTemplate).count() == 0

print("CATEGORY_MODULE_ALL_TESTS_PASSED")
