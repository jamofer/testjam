from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.project import Project, ProjectMember
from testjam.models.token import ApiToken
from testjam.models.user import User
from testjam.schemas.token import ApiTokenCreate, ApiTokenCreated, ApiTokenOut

user_router = APIRouter(prefix="/users/me/tokens", tags=["Tokens"])
project_router = APIRouter(prefix="/projects/{id}/tokens", tags=["Tokens"])


def _require_owner(project: Project, current: User, db: Session) -> None:
    if current.is_admin:
        return
    m = db.query(ProjectMember).filter_by(project_id=project.id, user_id=current.id).first()
    if not m or m.role != "owner":
        raise HTTPException(status_code=403, detail="Project owner or admin required")


# ── User tokens ───────────────────────────────────────────────────────────────

@user_router.get("", response_model=list[ApiTokenOut])
def list_user_tokens(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(ApiToken).filter(ApiToken.user_id == current.id).all()


@user_router.post("", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
def create_user_token(
    body: ApiTokenCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    raw, hashed, prefix = ApiToken.generate()
    t = ApiToken(name=body.name, token_hash=hashed, prefix=prefix, user_id=current.id, created_by=current.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return ApiTokenCreated(**ApiTokenOut.model_validate(t).model_dump(), token=raw)


@user_router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_token(token_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    t = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.user_id == current.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(t)
    db.commit()


# ── Project tokens ────────────────────────────────────────────────────────────

@project_router.get("", response_model=list[ApiTokenOut])
def list_project_tokens(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    return db.query(ApiToken).filter(ApiToken.project_id == id).all()


@project_router.post("", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
def create_project_token(
    id: int,
    body: ApiTokenCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    raw, hashed, prefix = ApiToken.generate()
    t = ApiToken(name=body.name, token_hash=hashed, prefix=prefix, project_id=id, created_by=current.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return ApiTokenCreated(**ApiTokenOut.model_validate(t).model_dump(), token=raw)


@project_router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_project_token(
    id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    t = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.project_id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(t)
    db.commit()
