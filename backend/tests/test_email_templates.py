"""Jinja-rendered email templates: rendering, escape, footer wiring."""
from __future__ import annotations

import pytest

from testjam.services import email_templates
from testjam.services.notification_events import NotificationEvent

ASSIGNED = NotificationEvent.EXECUTION_ASSIGNED.value
FINISHED = NotificationEvent.EXECUTION_FINISHED.value
FAILED = NotificationEvent.EXECUTION_FAILED.value


def _base_context() -> dict:
    return {
        "app_name": "Testjam",
        "site_url": "https://qa.example.com",
        "actor": "alice",
        "subject_object": "Smoke run",
        "link_in_app": "https://qa.example.com/executions/1/run",
    }


def test_assigned_subject_contains_app_name_and_title():
    subject, _, _ = email_templates.render(ASSIGNED, _base_context())
    assert subject == "[Testjam] You were assigned to 'Smoke run'"


def test_assigned_html_includes_actor_and_link():
    _, html, _ = email_templates.render(ASSIGNED, _base_context())
    assert "alice" in html
    assert "Smoke run" in html
    assert "https://qa.example.com/executions/1/run" in html


def test_assigned_text_includes_actor_and_link():
    _, _, text = email_templates.render(ASSIGNED, _base_context())
    assert "alice assigned you to 'Smoke run'." in text
    assert "https://qa.example.com/executions/1/run" in text


def test_html_autoescapes_malicious_title():
    context = _base_context()
    context["subject_object"] = "<script>alert('xss')</script>"
    _, html, _ = email_templates.render(FINISHED, context)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "alert(&#39;xss&#39;)" in html or "alert('xss')" not in html


def test_html_autoescapes_malicious_actor():
    context = _base_context()
    context["actor"] = "<img src=x onerror=alert(1)>"
    _, html, _ = email_templates.render(ASSIGNED, context)
    assert "<img src=x" not in html
    assert "&lt;img src=x" in html


def test_text_does_not_escape():
    """Plain-text body must contain raw characters as the user typed them."""
    context = _base_context()
    context["subject_object"] = "a < b & c"
    _, _, text = email_templates.render(FINISHED, context)
    assert "a < b & c" in text


def test_finished_renders_summary_block_when_provided():
    context = _base_context()
    context["summary"] = {"total": 5, "passed": 3, "failed": 1, "blocked": 1, "not_run": 0}
    _, html, text = email_templates.render(FINISHED, context)
    assert "Passed" in html and "3" in html
    assert "Failed" in html and "1" in html
    assert "Passed: 3" in text
    assert "Failed: 1" in text


def test_finished_renders_without_summary():
    _, html, _ = email_templates.render(FINISHED, _base_context())
    assert "Passed" not in html


def test_failed_uses_failure_styling_and_summary():
    context = _base_context()
    context["summary"] = {"total": 5, "passed": 0, "failed": 5, "blocked": 0, "not_run": 0}
    subject, html, text = email_templates.render(FAILED, context)
    assert subject == "[Testjam] Failed tests in 'Smoke run'"
    assert "5 failed out of 5" in text
    assert "<strong>5</strong>" in html


def test_footer_reason_and_preferences_link_present():
    _, html, text = email_templates.render(ASSIGNED, _base_context())
    assert "Manage email preferences" in html
    assert "Manage preferences:" in text
    assert "https://qa.example.com/profile" in html
    assert "https://qa.example.com/profile" in text
    assert "You're receiving this because you were assigned" in text


def test_footer_link_falls_back_when_no_site_url():
    context = _base_context()
    context["site_url"] = None
    _, html, text = email_templates.render(ASSIGNED, context)
    assert "/profile" in html
    assert "/profile" in text


def test_missing_required_variable_raises():
    with pytest.raises(Exception):
        email_templates.render(ASSIGNED, {"app_name": "Testjam"})


def test_build_preferences_url_strips_trailing_slash():
    assert email_templates.build_preferences_url("https://x.io/") == "https://x.io/profile"
    assert email_templates.build_preferences_url("https://x.io") == "https://x.io/profile"
    assert email_templates.build_preferences_url(None) == "/profile"
    assert email_templates.build_preferences_url("") == "/profile"
