from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_admin
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.settings import (
    AppSettingsOut,
    AppSettingsPublicOut,
    AppSettingsUpdate,
)
from testjam.services.backup import cleanup_archive, create_backup
from testjam.services.email import smtp_configured
from testjam.services.log_flusher import configure_from_settings as configure_log_flusher
from testjam.services.restore import RestoreSummary, restore_backup
from testjam.services.settings import get_settings

router = APIRouter(prefix="/settings", tags=["Settings"])

RESTORE_CONFIRM_TOKEN = "I-UNDERSTAND-THIS-REPLACES-ALL-DATA"


def _to_admin_out(s) -> AppSettingsOut:
    return AppSettingsOut(
        site_url=s.site_url,
        app_name=s.app_name,
        allow_registration=s.allow_registration,
        allow_user_self_delete=s.allow_user_self_delete,
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
        export_inline_attachment_mb=s.export_inline_attachment_mb,
        updated_at=s.updated_at,
    )


@router.get("/public", response_model=AppSettingsPublicOut)
def public_settings(db: Session = Depends(get_db)):
    s = get_settings(db)
    return AppSettingsPublicOut(
        app_name=s.app_name,
        allow_registration=s.allow_registration,
        allow_user_self_delete=s.allow_user_self_delete,
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


@router.get("/backup")
def download_backup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    artifact = create_backup(db, db.get_bind())
    background_tasks.add_task(cleanup_archive, artifact.path)
    return FileResponse(
        artifact.path,
        media_type="application/zip",
        filename=artifact.filename,
    )


@router.post("/restore", response_model=RestoreSummary)
async def upload_restore(
    file: UploadFile = File(...),
    confirm: str = Query(..., description=f"Must equal {RESTORE_CONFIRM_TOKEN}"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if confirm != RESTORE_CONFIRM_TOKEN:
        raise HTTPException(status_code=400, detail="Missing or invalid confirmation token")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload")
    return restore_backup(db.get_bind(), payload)
