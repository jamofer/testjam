"""Mention resolver + autocomplete endpoints.

Two endpoints, both scoped to a project:

- ``POST /projects/{id}/mentions/resolve`` — enriches a list of parsed tokens
  with display labels and URLs. Used by the MdViewer to render chips and by
  notification fan-out to filter recipients.
- ``GET  /projects/{id}/mentions/search`` — autocomplete used by the editor.
  Filters by ``kind`` (``user`` / ``bug`` / ``execution`` / ``case``) and a
  free-text query that matches either numeric id or name.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_project_access
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.mention import (
    MentionResolveRequest,
    MentionResolveResponse,
    MentionSearchHit,
    MentionSearchResponse,
)
from testjam.services import mention_resolver, mention_search


router = APIRouter(prefix="/projects", tags=["Mentions"])

SEARCH_LIMIT_MAX = 25
SEARCH_LIMIT_DEFAULT = 10


@router.post("/{id}/mentions/resolve", response_model=MentionResolveResponse)
def resolve_mentions(
    id: int,
    body: MentionResolveRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    resolved = mention_resolver.resolve(db, id, body.tokens)
    return MentionResolveResponse(mentions=resolved)


@router.get("/{id}/mentions/search", response_model=MentionSearchResponse)
def search_mentions(
    id: int,
    kind: str = Query(..., pattern="^(user|bug|execution|case)$"),
    q: str = "",
    limit: int = SEARCH_LIMIT_DEFAULT,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    capped = max(1, min(limit, SEARCH_LIMIT_MAX))
    hits = _dispatch_search(db, id, kind, q, capped)
    return MentionSearchResponse(hits=hits)


def _dispatch_search(db: Session, project_id: int, kind: str, query: str, limit: int) -> list[MentionSearchHit]:
    if kind == "user":
        return mention_search.search_users(db, project_id, query, limit)
    if kind == "bug":
        return mention_search.search_bugs(db, project_id, query, limit)
    if kind == "execution":
        return mention_search.search_executions(db, project_id, query, limit)
    if kind == "case":
        return mention_search.search_cases(db, project_id, query, limit)
    raise HTTPException(status_code=400, detail=f"Unsupported kind: {kind}")
