from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.notification_preference import (
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
)
from testjam.services import notification_preferences

router = APIRouter(
    prefix="/users/me/notification-preferences",
    tags=["Notification Preferences"],
)


def _require_known_event(event_type: str) -> None:
    if not notification_preferences.is_known_event(event_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown event_type: {event_type}",
        )


@router.get("", response_model=list[NotificationPreferenceOut])
def list_my_notification_preferences(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return notification_preferences.list_for_user(db, current.id)


@router.get("/{event_type}", response_model=NotificationPreferenceOut)
def get_my_notification_preference(
    event_type: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _require_known_event(event_type)
    preference = notification_preferences.get_or_create(db, current.id, event_type)
    db.commit()
    return preference


@router.put("/{event_type}", response_model=NotificationPreferenceOut)
def update_my_notification_preference(
    event_type: str,
    body: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _require_known_event(event_type)
    return notification_preferences.set_preference(
        db,
        current.id,
        event_type,
        in_app=body.in_app,
        email=body.email,
    )
