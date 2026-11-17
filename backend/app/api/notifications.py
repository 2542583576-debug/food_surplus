"""站内通知接口（需登录）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas.notification import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/api/notifications", tags=["站内通知"])


@router.get("/", response_model=list[NotificationOut], summary="我的通知")
def list_notifications(
    limit: int = 30,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current.id)
        .order_by(Notification.create_time.desc())
        .limit(limit)
        .all()
    )


@router.get("/unread-count", response_model=UnreadCountOut, summary="未读通知数")
def unread_count(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current.id, Notification.is_read.is_(False))
        .count()
    )
    return UnreadCountOut(unread=count)


@router.put("/read-all", summary="全部标为已读")
def read_all(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read.is_(False)
    ).update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"msg": "已全部标记为已读"}
