from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    get_unscoped_user,
    require_project_access,
    require_project_owner,
)
from testjam.database import get_db
from testjam.models.project import Project
from testjam.models.token import ApiToken
from testjam.models.user import User
from testjam.schemas.token import ApiTokenCreate, ApiTokenCreated, ApiTokenOut

user_router = APIRouter(prefix="/users/me/tokens", tags=["Tokens"])
project_router = APIRouter(prefix="/projects/{id}/tokens", tags=["Tokens"])


@user_router.get("", response_model=list[ApiTokenOut])
def list_user_tokens(db: Session = Depends(get_db), current: User = Depends(get_unscoped_user)):
    return db.query(ApiToken).filter(ApiToken.user_id == current.id).all()


@user_router.post("", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
def create_user_token(
    body: ApiTokenCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_unscoped_user),
):
    clash = (
        db.query(ApiToken)
        .filter(ApiToken.user_id == current.id, ApiToken.name == body.name)
        .first()
    )
    if clash:
        raise HTTPException(status_code=409, detail=f"Token '{body.name}' already exists")
    raw, hashed, prefix = ApiToken.generate()
    t = ApiToken(
        name=body.name,
        token_hash=hashed,
        prefix=prefix,
        user_id=current.id,
        created_by=current.id,
        expires_at=body.expires_at,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return ApiTokenCreated(**ApiTokenOut.model_validate(t).model_dump(), token=raw)


@user_router.post("/{token_id}/rotate", response_model=ApiTokenCreated)
def rotate_user_token(
    token_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_unscoped_user),
):
    token = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.user_id == current.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    raw = _rotate_token(token, db)
    return ApiTokenCreated(**ApiTokenOut.model_validate(token).model_dump(), token=raw)


@user_router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_token(token_id: int, db: Session = Depends(get_db), current: User = Depends(get_unscoped_user)):
    t = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.user_id == current.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(t)
    db.commit()


@project_router.get("", response_model=list[ApiTokenOut])
def list_project_tokens(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_owner(db, current, project.id)
    return db.query(ApiToken).filter(ApiToken.project_id == id).all()


@project_router.post("", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
def create_project_token(
    id: int,
    body: ApiTokenCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_owner(db, current, project.id)
    clash = (
        db.query(ApiToken)
        .filter(ApiToken.project_id == id, ApiToken.name == body.name)
        .first()
    )
    if clash:
        raise HTTPException(status_code=409, detail=f"Token '{body.name}' already exists")
    raw, hashed, prefix = ApiToken.generate()
    t = ApiToken(
        name=body.name,
        token_hash=hashed,
        prefix=prefix,
        project_id=id,
        created_by=current.id,
        expires_at=body.expires_at,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return ApiTokenCreated(**ApiTokenOut.model_validate(t).model_dump(), token=raw)


@project_router.post("/{token_id}/rotate", response_model=ApiTokenCreated)
def rotate_project_token(
    id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_owner(db, current, project.id)
    token = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.project_id == id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    raw = _rotate_token(token, db)
    return ApiTokenCreated(**ApiTokenOut.model_validate(token).model_dump(), token=raw)


@project_router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_project_token(
    id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_owner(db, current, project.id)
    t = db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.project_id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(t)
    db.commit()



def _rotate_token(token: ApiToken, db: Session) -> str:
    raw, hashed, prefix = ApiToken.generate()
    token.token_hash = hashed
    token.prefix = prefix
    token.last_used_at = None
    db.commit()
    db.refresh(token)
    return raw
