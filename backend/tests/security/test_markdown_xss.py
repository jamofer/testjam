"""Markdown → HTML renderer must neutralize XSS vectors.

`markdown_to_html.to_html` powers bug and execution report descriptions
served via public-report links. Anything that escapes the escape pipeline
becomes a stored-XSS hole the moment a report is shared. These tests
verify the two failure modes that matter:

* Literal HTML tags (``<script>``, event handlers) survive only as text.
* Markdown links with non-http(s)/mailto schemes degrade to plain text.
"""
import pytest

from testjam.services.integrations.markdown_to_html import to_html
from tests.security.payloads import (
    SAFE_URL_SCHEMES,
    UNSAFE_URL_SCHEMES,
    XSS_HTML_BODIES,
)


@pytest.mark.parametrize("payload", XSS_HTML_BODIES)
def test_inline_html_is_escaped(payload):
    rendered = to_html(payload).lower()

    for unescaped_tag in ("<script", "<svg", "<iframe", "<img", "<body"):
        assert unescaped_tag not in rendered, (
            f"renderer emitted live {unescaped_tag} from payload: {payload!r}"
        )


@pytest.mark.parametrize("scheme", UNSAFE_URL_SCHEMES)
def test_unsafe_link_schemes_are_demoted_to_text(scheme):
    rendered = to_html(f"[click]({scheme})").lower()

    assert "href=" not in rendered
    assert "javascript:" not in rendered
    assert "vbscript:" not in rendered
    assert "data:text/html" not in rendered
    assert "file://" not in rendered


@pytest.mark.parametrize("url", SAFE_URL_SCHEMES)
def test_safe_link_schemes_render_as_anchor(url):
    rendered = to_html(f"[click]({url})")

    assert f'href="{url}"' in rendered or f"href='{url}'" in rendered or 'href="' in rendered
    assert ">click</a>" in rendered
