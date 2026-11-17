"""门店自提点接口（公开）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Store, SurplusBag
from app.schemas.store import StoreWithBagsOut

router = APIRouter(prefix="/api/stores", tags=["自提门店"])


@router.get("/", response_model=list[StoreWithBagsOut], summary="门店自提点列表")
def list_stores(db: Session = Depends(get_db)):
    stores = db.query(Store).filter(Store.status == 1).order_by(Store.id).all()
    result = []
    for s in stores:
        bag_count = (
            db.query(SurplusBag)
            .filter(SurplusBag.store_id == s.id, SurplusBag.status == 1, SurplusBag.stock > 0)
            .count()
        )
        result.append(StoreWithBagsOut(
            id=s.id,
            store_name=s.store_name,
            address=s.address,
            phone=s.phone,
            cover=s.cover,
            business_hours=s.business_hours,
            longitude=s.longitude,
            latitude=s.latitude,
            bag_count=bag_count,
        ))
    return result
