"""SMTP email sender driven by AppSettings. Stdlib only."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from testjam.models.settings import AppSettings

log = logging.getLogger("testjam.email")


def smtp_configured(s: AppSettings) -> bool:
    return bool(s.smtp_host and s.smtp_from)


def send_email(s: AppSettings, to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Send a single message synchronously. Returns False on any failure (logged).

    Caller should run this from a background task — SMTP I/O blocks.
    """
    if not smtp_configured(s):
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = s.smtp_from
    msg["To"] = to
    if s.smtp_reply_to:
        msg["Reply-To"] = s.smtp_reply_to
    msg.set_content(text or "Open this email in an HTML-capable client.")
    msg.add_alternative(html, subtype="html")

    port = s.smtp_port or (465 if s.smtp_use_tls and (s.smtp_port == 465) else 587)
    try:
        if port == 465:
            with smtplib.SMTP_SSL(s.smtp_host, port, timeout=10) as smtp:
                if s.smtp_user and s.smtp_password:
                    smtp.login(s.smtp_user, s.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(s.smtp_host, port, timeout=10) as smtp:
                if s.smtp_use_tls:
                    smtp.starttls()
                if s.smtp_user and s.smtp_password:
                    smtp.login(s.smtp_user, s.smtp_password)
                smtp.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 — opaque failures should not crash the request
        log.warning("SMTP send failed to %s: %s", to, exc)
        return False
