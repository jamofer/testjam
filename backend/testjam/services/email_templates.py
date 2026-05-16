"""Jinja-rendered, locale-aware email templates.

Each notification event has four sibling files under
``testjam/templates/email/{locale}``:

- ``{event_type}.subject.txt``  — single-line subject
- ``{event_type}.message.txt``  — one-line in-app notification message
- ``{event_type}.html``         — body, extends ``_layout.html``; auto-escaped
- ``{event_type}.txt``          — plain-text body, not escaped (already text)

Two Jinja environments per locale: one with autoescape on for HTML, one off
for text. ``render(..., locale="es")`` selects the locale folder; missing or
unsupported locales fall back to English.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from testjam.services.notification_events import NotificationEvent

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "es", "ca", "gl", "eu")


def _make_environment(locale: str, autoescape: bool) -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR / locale),
        autoescape=jinja2.select_autoescape(["html"]) if autoescape else False,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


_html_envs = {locale: _make_environment(locale, autoescape=True) for locale in SUPPORTED_LOCALES}
_text_envs = {locale: _make_environment(locale, autoescape=False) for locale in SUPPORTED_LOCALES}


_FOOTER_REASONS: dict[str, dict[str, str]] = {
    "en": {
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
    },
    "es": {
        NotificationEvent.EXECUTION_ASSIGNED.value: (
            "Recibes este email porque te asignaron a una ejecución de pruebas."
        ),
        NotificationEvent.EXECUTION_FINISHED.value: (
            "Recibes este email porque una ejecución que creaste o te asignaron ha finalizado."
        ),
        NotificationEvent.EXECUTION_FAILED.value: (
            "Recibes este email porque una ejecución que creaste o te asignaron tuvo fallos."
        ),
        NotificationEvent.PASSWORD_RESET.value: (
            "Recibes este email porque se solicitó restablecer la contraseña de esta cuenta."
        ),
    },
    "ca": {
        NotificationEvent.EXECUTION_ASSIGNED.value: (
            "Reps aquest correu perquè t'han assignat a una execució de proves."
        ),
        NotificationEvent.EXECUTION_FINISHED.value: (
            "Reps aquest correu perquè una execució que has creat o que t'han assignat ha finalitzat."
        ),
        NotificationEvent.EXECUTION_FAILED.value: (
            "Reps aquest correu perquè una execució que has creat o que t'han assignat ha tingut errors."
        ),
        NotificationEvent.PASSWORD_RESET.value: (
            "Reps aquest correu perquè s'ha sol·licitat restablir la contrasenya d'aquest compte."
        ),
    },
    "gl": {
        NotificationEvent.EXECUTION_ASSIGNED.value: (
            "Recibes este correo porque che asignaron unha execución de probas."
        ),
        NotificationEvent.EXECUTION_FINISHED.value: (
            "Recibes este correo porque unha execución que creaches ou che asignaron rematou."
        ),
        NotificationEvent.EXECUTION_FAILED.value: (
            "Recibes este correo porque unha execución que creaches ou che asignaron tivo fallos."
        ),
        NotificationEvent.PASSWORD_RESET.value: (
            "Recibes este correo porque se solicitou restablecer o contrasinal desta conta."
        ),
    },
    "eu": {
        NotificationEvent.EXECUTION_ASSIGNED.value: (
            "Mezu hau jaso duzu proba-exekuzio bat esleitu zaizulako."
        ),
        NotificationEvent.EXECUTION_FINISHED.value: (
            "Mezu hau jaso duzu sortu zenuen edo esleitu zitzaizun exekuzio bat amaitu delako."
        ),
        NotificationEvent.EXECUTION_FAILED.value: (
            "Mezu hau jaso duzu sortu zenuen edo esleitu zitzaizun exekuzioak akatsak izan dituelako."
        ),
        NotificationEvent.PASSWORD_RESET.value: (
            "Mezu hau jaso duzu kontu honetarako pasahitza berrezartzeko eskaria egin delako."
        ),
    },
}

_GENERIC_FOOTER_REASON = {
    "en": "You're receiving this because notifications are enabled for your account.",
    "es": "Recibes este email porque las notificaciones están activas en tu cuenta.",
    "ca": "Reps aquest correu perquè les notificacions estan actives al teu compte.",
    "gl": "Recibes este correo porque as notificacións están activadas na túa conta.",
    "eu": "Mezu hau jaso duzu zure kontuan jakinarazpenak aktibatuta daudelako.",
}


def _resolve_locale(locale: str | None) -> str:
    if locale in SUPPORTED_LOCALES:
        return locale
    return DEFAULT_LOCALE


def build_preferences_url(site_url: str | None) -> str:
    base = (site_url or "").rstrip("/")
    if not base:
        return "/profile"
    return f"{base}/profile"


def _footer_reason(event_type: str, locale: str) -> str:
    reasons = _FOOTER_REASONS.get(locale, _FOOTER_REASONS[DEFAULT_LOCALE])
    return reasons.get(event_type, _GENERIC_FOOTER_REASON[locale])


def _build_full_context(event_type: str, context: dict[str, Any], locale: str) -> dict[str, Any]:
    return {
        "footer_reason": _footer_reason(event_type, locale),
        "preferences_url": build_preferences_url(context.get("site_url")),
        "summary": None,
        **context,
    }


def _render(env: jinja2.Environment, template: str, context: dict[str, Any]) -> str:
    return env.get_template(template).render(**context)


def render(
    event_type: str,
    context: dict[str, Any],
    locale: str | None = None,
) -> tuple[str, str, str, str]:
    """Return ``(subject, html, text, message)`` for the given event in *locale*.

    ``context`` must include ``app_name`` and any event-specific variables
    (``actor``, ``subject_object``, ``link_in_app``, optional ``summary``).
    ``footer_reason`` and ``preferences_url`` are filled in here.
    """
    resolved_locale = _resolve_locale(locale)
    full_context = _build_full_context(event_type, context, resolved_locale)
    html_env = _html_envs[resolved_locale]
    text_env = _text_envs[resolved_locale]
    subject = _render(text_env, f"{event_type}.subject.txt", full_context).strip()
    message = _render(text_env, f"{event_type}.message.txt", full_context).strip()
    html = _render(html_env, f"{event_type}.html", full_context)
    text = _render(text_env, f"{event_type}.txt", full_context)
    return subject, html, text, message
