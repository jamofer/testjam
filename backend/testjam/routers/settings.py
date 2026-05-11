from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_admin
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.settings import (
    AppSettingsOut,
    AppSettingsPublicOut,
    AppSettingsUpdate,
)
from testjam.services.email import smtp_configured
from testjam.services.log_flusher import configure_from_settings as configure_log_flusher
from testjam.services.settings import get_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


def _to_admin_out(s) -> AppSettingsOut:
    return AppSettingsOut(
        site_url=s.site_url,
        app_name=s.app_name,
        allow_registration=s.allow_registration,
        default_environment=s.default_environment,
        default_version_pattern=s.default_version_pattern,
        max_upload_mb=s.max_upload_mb,
        notifications_retention_days=s.notifications_retention_days,
        smtp_host=s.smtp_host,
        smtp_port=s.smtp_port,
        smtp_user=s.smtp_user,
        smtp_password_set=bool(s.smtp_password),
        smtp_from=s.smtp_from,
        smtp_reply_to=s.smtp_reply_to,
        smtp_use_tls=s.smtp_use_tls,
        ws_log_flush_ms=s.ws_log_flush_ms,
        updated_at=s.updated_at,
    )


@router.get("/public", response_model=AppSettingsPublicOut)
def public_settings(db: Session = Depends(get_db)):
    s = get_settings(db)
    return AppSettingsPublicOut(
        app_name=s.app_name,
        allow_registration=s.allow_registration,
        site_url=s.site_url,
        smtp_configured=smtp_configured(s),
    )


@router.get("", response_model=AppSettingsOut)
def read_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return _to_admin_out(get_settings(db))


@router.put("", response_model=AppSettingsOut)
def update_settings(
    body: AppSettingsUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    s = get_settings(db)
    payload = body.model_dump(exclude_unset=True)
    for field, value in payload.items():
        if field == "smtp_password" and value == "":
            s.smtp_password = None
            continue
        setattr(s, field, value)
    s.updated_by_id = current.id
    db.commit()
    db.refresh(s)
    configure_log_flusher(s)
    return _to_admin_out(s)
