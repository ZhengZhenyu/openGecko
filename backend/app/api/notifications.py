"""通知中心 API。

路由前缀 /api/notifications（在 main.py 注册）。
所有端点均需认证，按 user_id 隔离——只能操作自己的通知。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.timezone import utc_now
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationListOut, NotificationOut

router = APIRouter()


# ─── 列表 + 未读数 ────────────────────────────────────────────────────────────

@router.get("", response_model=NotificationListOut)
def list_notifications(
    unread_only: bool = Query(False, description="True = 仅返回未读通知"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的通知列表（分页），同时返回总数和未读总数。"""
    base_q = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = base_q.count()
    unread_count = base_q.filter(Notification.is_read == False).count()  # noqa: E712

    if unread_only:
        base_q = base_q.filter(Notification.is_read == False)  # noqa: E712

    items = (
        base_q
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return NotificationListOut(items=items, total=total, unread_count=unread_count)


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户未读通知数量（前端轮询专用，响应体极小）。"""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    return {"count": count}


# ─── 标记已读 ─────────────────────────────────────────────────────────────────

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单条通知为已读。"""
    notif = _get_own_notification(db, notification_id, current_user.id)
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = utc_now()
        db.commit()
        db.refresh(notif)
    return notif


@router.patch("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将当前用户所有未读通知标记为已读。"""
    now = utc_now()
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,  # noqa: E712
    ).update({"is_read": True, "read_at": now})
    db.commit()
    return {"detail": "全部已标记为已读"}


# ─── 删除 ─────────────────────────────────────────────────────────────────────

@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除单条通知。"""
    notif = _get_own_notification(db, notification_id, current_user.id)
    db.delete(notif)
    db.commit()


# ─── 内部辅助 ─────────────────────────────────────────────────────────────────

def _get_own_notification(db: Session, notification_id: int, user_id: int) -> Notification:
    """获取属于当前用户的通知，不存在则 404。"""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notif:
        raise HTTPException(404, "通知不存在")
    return notif
