"""Tiny markdown → HTML converter for Azure DevOps work-item descriptions.

ADO accepts HTML in ``System.Description``. We don't need full CommonMark —
just enough to keep bug reports readable: paragraphs, headings, bullet lists,
fenced code blocks, inline strong/em/code/link. Anything unrecognized passes
through HTML-escaped.
"""
from __future__ import annotations

import html
import re


_INLINE_PATTERN = re.compile(
    r"(\*\*(?P<bold>[^*]+)\*\*"
    r"|\*(?P<italic>[^*]+)\*"
    r"|`(?P<code>[^`]+)`"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\))"
)


def to_html(markdown: str) -> str:
    if not markdown:
        return ""
    lines = markdown.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() == "":
            index += 1
            continue
        if line.startswith("```"):
            block, advance = _consume_code_fence(lines, index)
            blocks.append(block)
            index = advance
            continue
        heading = _heading(line)
        if heading is not None:
            blocks.append(heading)
            index += 1
            continue
        if line.lstrip().startswith(("- ", "* ")):
            block, advance = _consume_list(lines, index)
            blocks.append(block)
            index = advance
            continue
        block, advance = _consume_paragraph(lines, index)
        blocks.append(block)
        index = advance
    return "".join(blocks)


def _heading(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.*)$", line)
    if not match:
        return None
    level = len(match.group(1))
    return f"<h{level}>{_inline(match.group(2))}</h{level}>"


def _consume_code_fence(lines: list[str], start: int) -> tuple[str, int]:
    fence = lines[start]
    language = fence.lstrip("`").strip()
    body_lines: list[str] = []
    cursor = start + 1
    while cursor < len(lines) and not lines[cursor].startswith("```"):
        body_lines.append(lines[cursor])
        cursor += 1
    end = cursor + 1 if cursor < len(lines) else cursor
    code = html.escape("\n".join(body_lines))
    if language:
        return f'<pre><code class="language-{html.escape(language)}">{code}</code></pre>', end
    return f"<pre><code>{code}</code></pre>", end


def _consume_list(lines: list[str], start: int) -> tuple[str, int]:
    items: list[str] = []
    cursor = start
    while cursor < len(lines):
        stripped = lines[cursor].lstrip()
        if not stripped.startswith(("- ", "* ")):
            break
        items.append(f"<li>{_inline(stripped[2:])}</li>")
        cursor += 1
    return f"<ul>{''.join(items)}</ul>", cursor


def _consume_paragraph(lines: list[str], start: int) -> tuple[str, int]:
    cursor = start
    buffer: list[str] = []
    while cursor < len(lines):
        line = lines[cursor]
        if line.strip() == "":
            break
        if line.startswith("```") or _heading(line) is not None:
            break
        if line.lstrip().startswith(("- ", "* ")):
            break
        buffer.append(line)
        cursor += 1
    text = " ".join(part.strip() for part in buffer)
    return f"<p>{_inline(text)}</p>", cursor


def _inline(text: str) -> str:
    if not text:
        return ""
    pieces: list[str] = []
    cursor = 0
    for match in _INLINE_PATTERN.finditer(text):
        if match.start() > cursor:
            pieces.append(html.escape(text[cursor:match.start()]))
        if match.group("bold") is not None:
            pieces.append(f"<strong>{html.escape(match.group('bold'))}</strong>")
        elif match.group("italic") is not None:
            pieces.append(f"<em>{html.escape(match.group('italic'))}</em>")
        elif match.group("code") is not None:
            pieces.append(f"<code>{html.escape(match.group('code'))}</code>")
        elif match.group("link_text") is not None:
            url = html.escape(match.group("link_url"), quote=True)
            text_part = html.escape(match.group("link_text"))
            pieces.append(f'<a href="{url}">{text_part}</a>')
        cursor = match.end()
    if cursor < len(text):
        pieces.append(html.escape(text[cursor:]))
    return "".join(pieces)
