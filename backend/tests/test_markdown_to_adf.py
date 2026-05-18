"""Unit tests for the markdown → ADF helper used by the Jira provider."""
from testjam.services.integrations.markdown_to_adf import to_adf


def test_empty_input_produces_empty_paragraph():
    doc = to_adf("")

    assert doc == {
        "version": 1,
        "type": "doc",
        "content": [{"type": "paragraph", "content": []}],
    }


def test_paragraph_collapses_wrapped_lines():
    doc = to_adf("Login crashes\nwhen offline")

    [block] = doc["content"]
    assert block["type"] == "paragraph"
    assert block["content"] == [{"type": "text", "text": "Login crashes when offline"}]


def test_heading_levels():
    doc = to_adf("## Title")

    [block] = doc["content"]
    assert block["type"] == "heading"
    assert block["attrs"] == {"level": 2}


def test_fenced_code_block_preserves_lines():
    body = "Steps:\n\n```python\nprint('x')\nprint('y')\n```\n"
    doc = to_adf(body)

    blocks = doc["content"]
    code = next(item for item in blocks if item["type"] == "codeBlock")
    assert code["attrs"] == {"language": "python"}
    assert code["content"] == [{"type": "text", "text": "print('x')\nprint('y')"}]


def test_bullet_list_items():
    doc = to_adf("- first\n- second")

    [block] = doc["content"]
    assert block["type"] == "bulletList"
    assert len(block["content"]) == 2
    assert block["content"][0]["content"][0]["type"] == "paragraph"


def test_inline_marks_in_paragraph():
    doc = to_adf("see **bold** and *em* and `code` and [docs](https://example.org)")

    [block] = doc["content"]
    marks = [
        node.get("marks", []) for node in block["content"] if "marks" in node
    ]
    assert {"type": "strong"} in marks[0]
    assert {"type": "em"} in marks[1]
    assert {"type": "code"} in marks[2]
    assert marks[3] == [{"type": "link", "attrs": {"href": "https://example.org"}}]
