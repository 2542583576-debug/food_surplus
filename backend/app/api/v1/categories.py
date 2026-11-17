from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.category import (
    AttributeTemplateCreate,
    AttributeTemplateOut,
    AttributeTemplateUpdate,
    CategoryCreate,
    CategoryMoveRequest,
    CategoryOut,
    CategoryTreeOut,
    CategoryUpdate,
)
from app.services import category_service as svc

router = APIRouter(dependencies=[Depends(get_current_user)])  # 整组需登录


# ---------- 树形分类 ----------

@router.get("", response_model=list[CategoryTreeOut], summary="分类树")
def get_tree(db: Session = Depends(get_db)):
    return svc.get_category_tree(db)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED, summary="新建分类")
def create(body: CategoryCreate, db: Session = Depends(get_db)):
    return svc.create_category(db, body)


@router.patch("/{category_id}", response_model=CategoryOut, summary="更新分类")
def update(category_id: int, body: CategoryUpdate, db: Session = Depends(get_db)):
    return svc.update_category(db, category_id, body)


@router.post("/{category_id}/move", response_model=CategoryOut, summary="移动/排序分类(拖拽)")
def move(category_id: int, body: CategoryMoveRequest, db: Session = Depends(get_db)):
    return svc.move_category(db, category_id, body)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除分类")
def delete(category_id: int, db: Session = Depends(get_db)):
    svc.delete_category(db, category_id)


# ---------- 属性模板 ----------

@router.get("/{category_id}/templates", response_model=list[AttributeTemplateOut], summary="分类下的属性模板")
def list_templates(category_id: int, db: Session = Depends(get_db)):
    return [svc.template_to_dict(t) for t in svc.list_templates_by_category(db, category_id)]


@router.post("/templates", response_model=AttributeTemplateOut, status_code=status.HTTP_201_CREATED, summary="新建属性模板")
def create_template(body: AttributeTemplateCreate, db: Session = Depends(get_db)):
    obj = svc.create_template(db, body)
    return svc.template_to_dict(obj)


@router.patch("/templates/{template_id}", response_model=AttributeTemplateOut, summary="更新属性模板")
def update_template(template_id: int, body: AttributeTemplateUpdate, db: Session = Depends(get_db)):
    obj = svc.update_template(db, template_id, body)
    return svc.template_to_dict(obj)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除属性模板")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    svc.delete_template(db, template_id)
