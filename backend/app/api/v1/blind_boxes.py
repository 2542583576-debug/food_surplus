from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.redis import get_redis
from app.db.session import get_db
from app.models import User
from app.schemas.blind_box import BlindBoxCreate, BlindBoxListOut, BlindBoxOut, BlindBoxStatusRequest, BlindBoxUpdate
from app.services import blind_box_service as svc

router = APIRouter(dependencies=[Depends(get_current_user)], tags=["盲盒管理"])


@router.get("", response_model=BlindBoxListOut, summary="盲盒列表(分页)")
def list_blind_boxes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    status: int | None = Query(default=None, description="0草稿 1上架 2下架 3售罄"),
    pickup_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, items = svc.list_blind_boxes(db, current_user.id, page, size, status, pickup_date)
    return BlindBoxListOut(total=total, items=items)


@router.post("", response_model=BlindBoxOut, status_code=status.HTTP_201_CREATED, summary="新建盲盒(草稿)")
def create_blind_box(body: BlindBoxCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return svc.create_blind_box(db, current_user.id, body.model_dump())


@router.patch("/{box_id}", response_model=BlindBoxOut, summary="更新盲盒(仅草稿/下架可改)")
def update_blind_box(
    box_id: int, body: BlindBoxUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return svc.update_blind_box(db, current_user.id, box_id, body.model_dump(exclude_unset=True))


@router.post("/{box_id}/status", response_model=BlindBoxOut, summary="上架/下架")
def change_status(
    box_id: int, body: BlindBoxStatusRequest,
    db: Session = Depends(get_db),
    r=Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    return svc.change_status(db, current_user.id, box_id, body.action, r=r)


@router.delete("/{box_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除盲盒")
def delete_blind_box(box_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc.delete_blind_box(db, current_user.id, box_id)
