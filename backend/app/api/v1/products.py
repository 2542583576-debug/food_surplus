from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.product import ProductCreate, ProductListOut, ProductOut, ProductUpdate
from app.services import product_service as svc

router = APIRouter(dependencies=[Depends(get_current_user)], tags=["商品管理"])


@router.get("", response_model=ProductListOut, summary="商品列表(分页)")
def list_products(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    category_id: int | None = None,
    keyword: str | None = None,
    is_on_sale: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, items = svc.list_products(db, current_user.id, page, size, category_id, keyword, is_on_sale)
    return ProductListOut(total=total, items=items)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED, summary="新建商品")
def create_product(body: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return svc.create_product(db, current_user.id, body.model_dump())


@router.patch("/{product_id}", response_model=ProductOut, summary="更新商品")
def update_product(
    product_id: int, body: ProductUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return svc.update_product(db, current_user.id, product_id, body.model_dump(exclude_unset=True))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc.delete_product(db, current_user.id, product_id)
