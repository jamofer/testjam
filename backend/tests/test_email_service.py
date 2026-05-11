"""SMTP send_email — header construction, reply-to handling, failure swallowing."""
from __future__ import annotations

from email.message import EmailMessage
from types import SimpleNamespace

import pytest

from testjam.services import email as email_service


def _settings(**overrides) -> SimpleNamespace:
    base = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": None,
        "smtp_password": None,
        "smtp_from": "noreply@example.com",
        "smtp_reply_to": None,
        "smtp_use_tls": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class _CapturingSMTP:
    """Stub SMTP/SMTP_SSL replacement that captures the message."""

    captured: EmailMessage | None = None

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def send_message(self, message: EmailMessage):
        type(self).captured = message


@pytest.fixture(autouse=True)
def _reset_captured():
    _CapturingSMTP.captured = None
    yield
    _CapturingSMTP.captured = None


def test_send_email_returns_false_when_smtp_unconfigured():
    settings = _settings(smtp_host=None)
    assert email_service.send_email(settings, "to@x.com", "S", "<p>h</p>") is False


def test_send_email_sets_basic_headers(monkeypatch):
    monkeypatch.setattr(email_service.smtplib, "SMTP", _CapturingSMTP)
    settings = _settings()
    ok = email_service.send_email(
        settings, "to@x.com", "Hello", "<p>html</p>", "plain text",
    )
    assert ok is True
    msg = _CapturingSMTP.captured
    assert msg is not None
    assert msg["Subject"] == "Hello"
    assert msg["From"] == "noreply@example.com"
    assert msg["To"] == "to@x.com"
    assert msg["Reply-To"] is None


def test_send_email_sets_reply_to_when_configured(monkeypatch):
    monkeypatch.setattr(email_service.smtplib, "SMTP", _CapturingSMTP)
    settings = _settings(smtp_reply_to="support@example.com")
    email_service.send_email(settings, "to@x.com", "Hi", "<p>x</p>")
    assert _CapturingSMTP.captured["Reply-To"] == "support@example.com"


def test_send_email_uses_ssl_on_port_465(monkeypatch):
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", _CapturingSMTP)
    monkeypatch.setattr(email_service.smtplib, "SMTP", _CapturingSMTP)
    settings = _settings(smtp_port=465, smtp_use_tls=True)
    email_service.send_email(settings, "to@x.com", "Hi", "<p>x</p>")
    assert _CapturingSMTP.captured is not None


def test_send_email_swallows_smtp_errors(monkeypatch):
    class _Boom(_CapturingSMTP):
        def send_message(self, message):
            raise RuntimeError("smtp broke")

    monkeypatch.setattr(email_service.smtplib, "SMTP", _Boom)
    settings = _settings()
    assert email_service.send_email(settings, "to@x.com", "Hi", "<p>x</p>") is False
