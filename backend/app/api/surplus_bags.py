from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.surplus_bag import SurplusBag
from app.schemas.surplus_bag import SurplusBagCreate, SurplusBagUpdate, SurplusBagOut
from app.api.deps import get_current_user, require_store_admin

router = APIRouter(prefix="/api/surplus-bags", tags=["惜食余量魔法袋"])

# 魔法袋列表（公开浏览）
@router.get("/", response_model=List[SurplusBagOut])
def list_bag(store_id: int | None = None, page: int = Query(1), size: int = Query(10), db: Session = Depends(get_db)):
    q = db.query(SurplusBag).filter(SurplusBag.status == 1)
    if store_id:
        q = q.filter(SurplusBag.store_id == store_id)
    q = q.order_by(SurplusBag.id.desc())
    return q.offset((page - 1) * size).limit(size).all()

@router.get("/{bag_id}", response_model=SurplusBagOut)
def get_bag(bag_id: int, db: Session = Depends(get_db)):
    b = db.query(SurplusBag).filter(SurplusBag.id == bag_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="魔法袋不存在")
    return b

# 新增魔法袋：门店管理员，自动归属自己门店
@router.post("/", response_model=SurplusBagOut)
def create_bag(
    bag_in: SurplusBagCreate,
    db: Session = Depends(get_db),
    current = Depends(require_store_admin)
):
    # 强制魔法袋store_id = 当前管理员绑定门店，不能随便填别的门店
    bag_data = bag_in.model_dump()
    bag_data["store_id"] = current.store_id
    new_bag = SurplusBag(**bag_data)
    db.add(new_bag)
    db.commit()
    db.refresh(new_bag)
    return new_bag

# 修改魔法袋：只能修改本店的
@router.put("/{bag_id}", response_model=SurplusBagOut)
def update_bag(
    bag_id: int,
    bag_in: SurplusBagUpdate,
    db: Session = Depends(get_db),
    current = Depends(require_store_admin)
):
    b = db.query(SurplusBag).filter(SurplusBag.id == bag_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="魔法袋不存在")
    if b.store_id != current.store_id:
        raise HTTPException(status_code=403, detail="只能管理本店魔法袋")
    for k, v in bag_in.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return b

# 删除魔法袋
@router.delete("/{bag_id}")
def delete_bag(
    bag_id: int,
    db: Session = Depends(get_db),
    current = Depends(require_store_admin)
):
    b = db.query(SurplusBag).filter(SurplusBag.id == bag_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="魔法袋不存在")
    if b.store_id != current.store_id:
        raise HTTPException(status_code=403, detail="只能管理本店魔法袋")
    db.delete(b)
    db.commit()
    return {"msg":"删除成功"}
