"""Jinja-rendered email templates.

Each notification event has three sibling files under ``testjam/templates/email``:

- ``{event_type}.subject.txt`` — single-line subject
- ``{event_type}.html``        — body, extends ``_layout.html``; auto-escaped
- ``{event_type}.txt``         — plain-text body, not escaped (already text)

Two Jinja environments are kept because the HTML one enables autoescape (which
turns ``<script>`` into ``&lt;script&gt;``) while the text one must emit the
raw characters the user wrote.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from testjam.services.notification_events import NotificationEvent

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

_html_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
    autoescape=jinja2.select_autoescape(["html"]),
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

_text_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
    autoescape=False,
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

FOOTER_REASONS: dict[str, str] = {
    NotificationEvent.EXECUTION_ASSIGNED.value: (
        "You're receiving this because you were assigned to a test execution."
    ),
    NotificationEvent.EXECUTION_FINISHED.value: (
        "You're receiving this because a test execution you created or were "
        "assigned to has finished."
    ),
    NotificationEvent.EXECUTION_FAILED.value: (
        "You're receiving this because a test execution you created or were "
        "assigned to had failed tests."
    ),
    NotificationEvent.PASSWORD_RESET.value: (
        "You're receiving this because a password reset was requested for this account."
    ),
}

_GENERIC_FOOTER_REASON = "You're receiving this because notifications are enabled for your account."


def build_preferences_url(site_url: str | None) -> str:
    base = (site_url or "").rstrip("/")
    if not base:
        return "/profile"
    return f"{base}/profile"


def _build_full_context(event_type: str, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "footer_reason": FOOTER_REASONS.get(event_type, _GENERIC_FOOTER_REASON),
        "preferences_url": build_preferences_url(context.get("site_url")),
        "summary": None,
        **context,
    }


def _render_subject(event_type: str, context: dict[str, Any]) -> str:
    return (
        _text_environment.get_template(f"{event_type}.subject.txt")
        .render(**context)
        .strip()
    )


def _render_html(event_type: str, context: dict[str, Any]) -> str:
    return _html_environment.get_template(f"{event_type}.html").render(**context)


def _render_text(event_type: str, context: dict[str, Any]) -> str:
    return _text_environment.get_template(f"{event_type}.txt").render(**context)


def render(event_type: str, context: dict[str, Any]) -> tuple[str, str, str]:
    """Return ``(subject, html, text)`` for the given event.

    ``context`` must include ``app_name`` and any event-specific variables
    (``actor``, ``subject_object``, ``link_in_app``, optional ``summary``).
    ``footer_reason`` and ``preferences_url`` are filled in here.
    """
    full_context = _build_full_context(event_type, context)
    subject = _render_subject(event_type, full_context)
    html = _render_html(event_type, full_context)
    text = _render_text(event_type, full_context)
    return subject, html, text
