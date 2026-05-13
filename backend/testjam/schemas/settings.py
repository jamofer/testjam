from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AppSettingsPublicOut(BaseModel):
    """Anon-readable subset used for branding + register gate."""
    app_name: str
    allow_registration: bool
    allow_user_self_delete: bool = False
    site_url: str | None = None
    smtp_configured: bool = False


class AppSettingsOut(BaseModel):
    """Admin-only payload. Secrets (smtp_password) are masked."""
    model_config = ConfigDict(from_attributes=True)

    site_url: str | None
    app_name: str
    allow_registration: bool
    allow_user_self_delete: bool
    default_environment: str | None
    default_version_pattern: str | None
    max_upload_mb: int
    notifications_retention_days: int
    smtp_host: str | None
    smtp_port: int | None
    smtp_user: str | None
    smtp_password_set: bool
    smtp_from: str | None
    smtp_reply_to: str | None
    smtp_use_tls: bool
    ws_log_flush_ms: int
    export_inline_attachment_mb: int
    updated_at: datetime


class AppSettingsUpdate(BaseModel):
    """Partial update. None means "leave unchanged"; empty string means "clear".

    For smtp_password: pass None to keep, "" to clear, any string to replace.
    """
    site_url: str | None = None
    app_name: str | None = None
    allow_registration: bool | None = None
    allow_user_self_delete: bool | None = None
    default_environment: str | None = None
    default_version_pattern: str | None = None
    max_upload_mb: int | None = None
    notifications_retention_days: int | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_reply_to: str | None = None
    smtp_use_tls: bool | None = None
    ws_log_flush_ms: int | None = None
    export_inline_attachment_mb: int | None = None
