import json

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AttributeTemplate, Category, Product


def _load_templates(db: Session, category_id: int) -> list[dict]:
    """合并分类自身的模板；暂不做父级继承（树继承留给后续增强）"""
    templates = db.scalars(
        select(AttributeTemplate).where(AttributeTemplate.category_id == category_id)
    ).all()
    fields: list[dict] = []
    for t in templates:
        fields.extend(json.loads(t.attribute_schema))
    return fields


def validate_attributes(db: Session, category_id: int, attributes: dict) -> None:
    """按分类属性模板校验商品属性值：required 必填 + 类型检查"""
    fields = _load_templates(db, category_id)
    for f in fields:
        key, label, ftype = f["key"], f["label"], f["type"]
        value = attributes.get(key)
        missing = value is None or value == "" or value == []
        if f.get("required") and missing:
            raise HTTPException(status_code=400, detail=f"属性[{label}]为必填项")
        if missing:
            continue
        if ftype == "number" and not isinstance(value, (int, float)):
            raise HTTPException(status_code=400, detail=f"属性[{label}]必须为数字")
        if ftype == "boolean" and not isinstance(value, bool):
            raise HTTPException(status_code=400, detail=f"属性[{label}]必须为布尔值")
        if ftype in ("select", "multiselect"):
            values = value if isinstance(value, list) else [value]
            allowed = set(f.get("options", []))
            invalid = [v for v in values if v not in allowed]
            if invalid:
                raise HTTPException(status_code=400, detail=f"属性[{label}]的值 {invalid} 不在可选项中")
            if ftype == "select" and isinstance(value, list):
                raise HTTPException(status_code=400, detail=f"属性[{label}]为单选，不能传数组")


def get_product_or_404(db: Session, product_id: int, merchant_id: int) -> Product:
    obj = db.get(Product, product_id)
    if obj is None or obj.merchant_id != merchant_id:
        raise HTTPException(status_code=404, detail="商品不存在")
    return obj


def create_product(db: Session, merchant_id: int, data: dict) -> Product:
    category = db.get(Category, data["category_id"])
    if category is None:
        raise HTTPException(status_code=400, detail="分类不存在")
    validate_attributes(db, data["category_id"], data.get("attributes") or {})
    obj = Product(merchant_id=merchant_id, **data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_product(db: Session, merchant_id: int, product_id: int, data: dict) -> Product:
    obj = get_product_or_404(db, product_id, merchant_id)
    if "category_id" in data and data["category_id"] != obj.category_id:
        category = db.get(Category, data["category_id"])
        if category is None:
            raise HTTPException(status_code=400, detail="分类不存在")
        # 换分类后用新分类模板重新校验属性
        validate_attributes(db, data["category_id"], data.get("attributes") if "attributes" in data else json.loads(json.dumps(obj.attributes or {})))
    elif "attributes" in data:
        validate_attributes(db, obj.category_id, data["attributes"])
    for field, value in data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_product(db: Session, merchant_id: int, product_id: int) -> None:
    obj = get_product_or_404(db, product_id, merchant_id)
    db.delete(obj)
    db.commit()


def list_products(
    db: Session, merchant_id: int, page: int, size: int,
    category_id: int | None = None, keyword: str | None = None, is_on_sale: bool | None = None,
) -> tuple[int, list[Product]]:
    stmt = select(Product).where(Product.merchant_id == merchant_id)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if keyword:
        stmt = stmt.where(Product.name.like(f"%{keyword}%"))
    if is_on_sale is not None:
        stmt = stmt.where(Product.is_on_sale == is_on_sale)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Product.id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return total, list(items)
