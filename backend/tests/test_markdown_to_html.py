"""Unit tests for the markdown → HTML helper used by Azure DevOps."""
from testjam.services.integrations.markdown_to_html import to_html


def test_empty_input_returns_empty_string():
    assert to_html("") == ""


def test_paragraph_collapses_wrapped_lines():
    assert to_html("Login crashes\nwhen offline") == "<p>Login crashes when offline</p>"


def test_heading_levels():
    assert to_html("## Title") == "<h2>Title</h2>"


def test_fenced_code_block_escapes_html():
    body = "```python\nprint('<x>')\n```"

    out = to_html(body)

    assert out == '<pre><code class="language-python">print(&#x27;&lt;x&gt;&#x27;)</code></pre>'


def test_bullet_list_items():
    out = to_html("- first\n- second")

    assert out == "<ul><li>first</li><li>second</li></ul>"


def test_inline_marks():
    out = to_html("see **bold** and *em* and `code` and [docs](https://example.org)")

    assert out == (
        "<p>see <strong>bold</strong> and <em>em</em> and <code>code</code> "
        'and <a href="https://example.org">docs</a></p>'
    )


def test_plain_text_is_html_escaped():
    assert to_html("a <b> c & d") == "<p>a &lt;b&gt; c &amp; d</p>"
