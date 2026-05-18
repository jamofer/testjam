"""Minimal markdown → Atlassian Document Format converter.

Jira Cloud's REST v3 API rejects raw markdown — bodies must be ADF JSON. A
full converter would round-trip CommonMark; we ship the subset that covers
typical bug reports: paragraphs, headings, bullet lists, fenced code blocks,
and inline ``**bold**`` / ``*italic*`` / ``` `code` ``` / ``[text](url)``.

Anything that doesn't match a recognized pattern falls back to a plain
paragraph so users never see an empty ticket body.
"""
from __future__ import annotations

import re
from typing import Any


ADF_VERSION = 1


def to_adf(markdown: str) -> dict[str, Any]:
    blocks = _parse_blocks(markdown or "")
    if not blocks:
        blocks = [_paragraph([])]
    return {"version": ADF_VERSION, "type": "doc", "content": blocks}


def _parse_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    out: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_blank(line):
            index += 1
            continue
        if line.startswith("```"):
            block, advance = _consume_code_fence(lines, index)
            out.append(block)
            index = advance
            continue
        heading = _match_heading(line)
        if heading is not None:
            out.append(heading)
            index += 1
            continue
        if line.lstrip().startswith(("- ", "* ")):
            block, advance = _consume_bullet_list(lines, index)
            out.append(block)
            index = advance
            continue
        block, advance = _consume_paragraph(lines, index)
        out.append(block)
        index = advance
    return out


def _consume_code_fence(lines: list[str], start: int) -> tuple[dict[str, Any], int]:
    fence = lines[start]
    language = fence.lstrip("`").strip() or None
    body_lines: list[str] = []
    cursor = start + 1
    while cursor < len(lines) and not lines[cursor].startswith("```"):
        body_lines.append(lines[cursor])
        cursor += 1
    end = cursor + 1 if cursor < len(lines) else cursor
    attrs: dict[str, Any] = {}
    if language:
        attrs["language"] = language
    return {
        "type": "codeBlock",
        "attrs": attrs,
        "content": [{"type": "text", "text": "\n".join(body_lines)}],
    }, end


def _match_heading(line: str) -> dict[str, Any] | None:
    match = re.match(r"^(#{1,6})\s+(.*)$", line)
    if not match:
        return None
    level = len(match.group(1))
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": _inline(match.group(2)),
    }


def _consume_bullet_list(lines: list[str], start: int) -> tuple[dict[str, Any], int]:
    items: list[dict[str, Any]] = []
    cursor = start
    while cursor < len(lines):
        stripped = lines[cursor].lstrip()
        if not stripped.startswith(("- ", "* ")):
            break
        text = stripped[2:]
        items.append({
            "type": "listItem",
            "content": [_paragraph(_inline(text))],
        })
        cursor += 1
    return {"type": "bulletList", "content": items}, cursor


def _consume_paragraph(lines: list[str], start: int) -> tuple[dict[str, Any], int]:
    cursor = start
    buffer: list[str] = []
    while cursor < len(lines):
        line = lines[cursor]
        if _is_blank(line):
            break
        if line.startswith("```") or _match_heading(line) is not None:
            break
        if line.lstrip().startswith(("- ", "* ")):
            break
        buffer.append(line)
        cursor += 1
    text = " ".join(part.strip() for part in buffer)
    return _paragraph(_inline(text)), cursor


_INLINE_PATTERN = re.compile(
    r"(\*\*(?P<bold>[^*]+)\*\*"
    r"|\*(?P<italic>[^*]+)\*"
    r"|`(?P<code>[^`]+)`"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\))"
)


def _inline(text: str) -> list[dict[str, Any]]:
    if not text:
        return []
    pieces: list[dict[str, Any]] = []
    cursor = 0
    for match in _INLINE_PATTERN.finditer(text):
        if match.start() > cursor:
            pieces.append(_text_node(text[cursor:match.start()]))
        if match.group("bold") is not None:
            pieces.append(_text_node(match.group("bold"), marks=[{"type": "strong"}]))
        elif match.group("italic") is not None:
            pieces.append(_text_node(match.group("italic"), marks=[{"type": "em"}]))
        elif match.group("code") is not None:
            pieces.append(_text_node(match.group("code"), marks=[{"type": "code"}]))
        elif match.group("link_text") is not None:
            url = match.group("link_url")
            pieces.append(_text_node(
                match.group("link_text"),
                marks=[{"type": "link", "attrs": {"href": url}}],
            ))
        cursor = match.end()
    if cursor < len(text):
        pieces.append(_text_node(text[cursor:]))
    return pieces


def _text_node(text: str, *, marks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


def _paragraph(content: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "paragraph", "content": content}


def _is_blank(line: str) -> bool:
    return line.strip() == ""
