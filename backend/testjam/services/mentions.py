"""Mention parser shared with the frontend.

Recognized sigils inside a markdown body:

- ``@username``         user
- ``#42``               bug
- ``!17``               execution
- ``!17/91``            test result inside execution 17
- ``!17/91/3``          step result inside that result
- ``~91``               test case (definition)

Boundary rule: a sigil must be preceded by whitespace or start of string,
so ``email@host`` never matches. Tokens inside fenced or inline code are
ignored — code spans are stripped before tokenization.

The output schema mirrors ``frontend/src/lib/mentions/parser.js`` so backend
notification fan-out and frontend rendering see the same tokens.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


MentionKind = Literal["user", "bug", "execution", "result", "step_result", "case"]


@dataclass(frozen=True)
class Mention:
    kind: MentionKind
    raw: str
    start: int
    end: int
    slug: str | None = None
    id: int | None = None
    sub_ids: tuple[int, ...] = field(default_factory=tuple)


_USER_PATTERN = re.compile(r"(?<!\S)@([a-zA-Z0-9_.\-]+)")
_BUG_PATTERN = re.compile(r"(?<!\S)#(\d+)\b")
_EXECUTION_PATTERN = re.compile(r"(?<!\S)!(\d+)(?:/(\d+)(?:/(\d+))?)?\b")
_CASE_PATTERN = re.compile(r"(?<!\S)~(\d+)\b")

_FENCED_CODE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE = re.compile(r"`[^`\n]+`")


def parse(text: str) -> list[Mention]:
    if not text:
        return []
    masked = _mask_code(text)
    found: list[Mention] = []
    found.extend(_match_users(masked))
    found.extend(_match_bugs(masked))
    found.extend(_match_executions(masked))
    found.extend(_match_cases(masked))
    found.sort(key=lambda m: m.start)
    return _dedupe(found)


def usernames(text: str) -> list[str]:
    return [m.slug for m in parse(text) if m.kind == "user" and m.slug]


def _match_users(text: str) -> list[Mention]:
    return [
        Mention(
            kind="user",
            raw=match.group(0),
            slug=match.group(1),
            start=match.start(),
            end=match.end(),
        )
        for match in _USER_PATTERN.finditer(text)
    ]


def _match_bugs(text: str) -> list[Mention]:
    return [
        Mention(
            kind="bug",
            raw=match.group(0),
            id=int(match.group(1)),
            start=match.start(),
            end=match.end(),
        )
        for match in _BUG_PATTERN.finditer(text)
    ]


def _match_executions(text: str) -> list[Mention]:
    out: list[Mention] = []
    for match in _EXECUTION_PATTERN.finditer(text):
        execution_id = int(match.group(1))
        result_id = int(match.group(2)) if match.group(2) else None
        step_result_id = int(match.group(3)) if match.group(3) else None
        if step_result_id is not None:
            out.append(Mention(
                kind="step_result", raw=match.group(0),
                id=execution_id, sub_ids=(result_id, step_result_id),
                start=match.start(), end=match.end(),
            ))
        elif result_id is not None:
            out.append(Mention(
                kind="result", raw=match.group(0),
                id=execution_id, sub_ids=(result_id,),
                start=match.start(), end=match.end(),
            ))
        else:
            out.append(Mention(
                kind="execution", raw=match.group(0),
                id=execution_id,
                start=match.start(), end=match.end(),
            ))
    return out


def _match_cases(text: str) -> list[Mention]:
    return [
        Mention(
            kind="case",
            raw=match.group(0),
            id=int(match.group(1)),
            start=match.start(),
            end=match.end(),
        )
        for match in _CASE_PATTERN.finditer(text)
    ]


def _mask_code(text: str) -> str:
    masked = _FENCED_CODE.sub(lambda m: " " * len(m.group(0)), text)
    return _INLINE_CODE.sub(lambda m: " " * len(m.group(0)), masked)


def _dedupe(mentions: list[Mention]) -> list[Mention]:
    seen: set[tuple] = set()
    unique: list[Mention] = []
    for mention in mentions:
        key = (mention.kind, mention.slug, mention.id, mention.sub_ids)
        if key in seen:
            continue
        seen.add(key)
        unique.append(mention)
    return unique
