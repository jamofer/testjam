"""ANSI colour helpers respect TTY detection + NO_COLOR/FORCE_COLOR."""
from orchestrator import color


def test_paint_returns_plain_when_disabled():
    assert color.paint("ok", "green", enabled=False) == "ok"


def test_paint_wraps_with_ansi_codes_when_enabled():
    out = color.paint("ok", "green", enabled=True)
    assert out.startswith("\033[")
    assert out.endswith("\033[0m")


def test_paint_unknown_style_returns_plain():
    assert color.paint("ok", "magenta-ish", enabled=True) == "ok"


def test_supports_color_respects_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert color.supports_color() is False


def test_supports_color_respects_force_color(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert color.supports_color() is True
