from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AttributeTemplate, Category
from app.schemas.category import (
    AttributeTemplateCreate,
    AttributeTemplateUpdate,
    CategoryCreate,
    CategoryMoveRequest,
    CategoryUpdate,
)
from app.utils.tree import build_tree, collect_descendant_ids
import json


# ---------- 分类 ----------

def get_category_or_404(db: Session, category_id: int) -> Category:
    obj = db.get(Category, category_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    return obj


def create_category(db: Session, body: CategoryCreate) -> Category:
    if body.parent_id is not None:
        get_category_or_404(db, body.parent_id)  # 父分类必须存在
    obj = Category(
        parent_id=body.parent_id,
        name=body.name,
        icon=body.icon,
        sort_order=body.sort_order,
        is_enabled=body.is_enabled,
        remark=body.remark,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_category(db: Session, category_id: int, body: CategoryUpdate) -> Category:
    obj = get_category_or_404(db, category_id)
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def move_category(db: Session, category_id: int, body: CategoryMoveRequest) -> Category:
    """拖拽移动/排序：校验目标父分类不是自己或自己的子孙（防循环引用）"""
    obj = get_category_or_404(db, category_id)
    if body.parent_id is not None:
        if body.parent_id == category_id:
            raise HTTPException(status_code=400, detail="不能将分类移动到自己之下")
        all_categories = db.scalars(select(Category)).all()
        descendants = collect_descendant_ids(all_categories, category_id)
        if body.parent_id in descendants:
            raise HTTPException(status_code=400, detail="不能将分类移动到自己的子孙分类之下")
        get_category_or_404(db, body.parent_id)
    obj.parent_id = body.parent_id
    obj.sort_order = body.sort_order
    db.commit()
    db.refresh(obj)
    return obj


def delete_category(db: Session, category_id: int) -> None:
    obj = get_category_or_404(db, category_id)
    if obj.children:
        raise HTTPException(status_code=400, detail="存在子分类，请先删除或移动子分类")
    db.delete(obj)  # 属性模板随 CASCADE 级联删除
    db.commit()


def get_category_tree(db: Session) -> list[dict]:
    categories = db.scalars(select(Category).order_by(Category.sort_order, Category.id)).all()
    return build_tree(categories)


# ---------- 属性模板 ----------

def template_to_dict(obj: AttributeTemplate) -> dict:
    """ORM 对象 → 输出字典（解析 attribute_schema JSON 串）"""
    return {
        "id": obj.id,
        "category_id": obj.category_id,
        "name": obj.name,
        "fields": json.loads(obj.attribute_schema),
    }


def create_template(db: Session, body: AttributeTemplateCreate) -> AttributeTemplate:
    get_category_or_404(db, body.category_id)
    obj = AttributeTemplate(
        category_id=body.category_id,
        name=body.name,
        attribute_schema=json.dumps([f.model_dump() for f in body.fields], ensure_ascii=False),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_template(db: Session, template_id: int, body: AttributeTemplateUpdate) -> AttributeTemplate:
    obj = db.get(AttributeTemplate, template_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="属性模板不存在")
    if body.name is not None:
        obj.name = body.name
    if body.fields is not None:
        obj.attribute_schema = json.dumps([f.model_dump() for f in body.fields], ensure_ascii=False)
    db.commit()
    db.refresh(obj)
    return obj


def delete_template(db: Session, template_id: int) -> None:
    obj = db.get(AttributeTemplate, template_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="属性模板不存在")
    db.delete(obj)
    db.commit()


def list_templates_by_category(db: Session, category_id: int) -> list[AttributeTemplate]:
    return list(db.scalars(
        select(AttributeTemplate).where(AttributeTemplate.category_id == category_id)
    ).all())
