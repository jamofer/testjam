from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.auth.security import decode_token
from testjam.database import get_db
from testjam.models.notification import Notification
from testjam.models.user import User
from testjam.realtime import manager
from testjam.schemas.notification import NotificationOut, UnreadCount

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    skip: int = 0,
    limit: int = 50,
    only_unread: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    limit = min(limit, 200)
    q = db.query(Notification).filter(Notification.user_id == current.id)
    if only_unread:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    return q.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(skip).limit(limit).all()


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    n = (
        db.query(Notification)
        .filter(Notification.user_id == current.id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    return UnreadCount(unread=n)


@router.post("/{id}/read", response_model=NotificationOut)
def mark_read(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == id, Notification.user_id == current.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


@router.post("/read-all", response_model=UnreadCount)
def mark_all_read(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.user_id == current.id,
        Notification.is_read == False,  # noqa: E712
    ).update({Notification.is_read: True})
    db.commit()
    return UnreadCount(unread=0)


@router.websocket("/ws")
async def notifications_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    username = decode_token(token)
    user = (
        db.query(User).filter(User.username == username, User.is_active == True).first()  # noqa: E712
        if username
        else None
    )
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user.id, websocket)
