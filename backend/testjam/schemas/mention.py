from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MentionKind = Literal["user", "bug", "execution", "result", "step_result", "case"]


class MentionTokenIn(BaseModel):
    kind: MentionKind
    slug: str | None = None
    id: int | None = None
    sub_ids: list[int] = Field(default_factory=list)


class MentionResolveRequest(BaseModel):
    tokens: list[MentionTokenIn] = Field(default_factory=list)


class MentionPart(BaseModel):
    kind: MentionKind
    label: str
    url: str | None = None


class ResolvedMentionOut(BaseModel):
    kind: MentionKind
    slug: str | None = None
    id: int | None = None
    sub_ids: list[int] = Field(default_factory=list)
    label: str | None = None
    description: str | None = None
    url: str | None = None
    parts: list[MentionPart] = Field(default_factory=list)
    accessible: bool = False


class MentionResolveResponse(BaseModel):
    mentions: list[ResolvedMentionOut] = Field(default_factory=list)


class MentionSearchHit(BaseModel):
    kind: MentionKind
    id: int | None = None
    sub_ids: list[int] = Field(default_factory=list)
    slug: str | None = None
    label: str
    description: str | None = None
    url: str | None = None


class MentionSearchResponse(BaseModel):
    hits: list[MentionSearchHit] = Field(default_factory=list)
