from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import update
from sqlalchemy.orm import Session

from testjam.auth.security import decode_token, is_session_current
from testjam.core.logging import set_current_user_id
from testjam.database import get_db
from testjam.models.project import Project
from testjam.models.token import ApiToken
from testjam.models.user import User
from testjam.services.permissions import VALID_ROLES, effective_role, is_project_writer

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
TOKEN_LAST_USED_RESOLUTION = timedelta(minutes=1)


@dataclass
class AuthContext:
    user: User
    # If set, the active credential is a project-scoped API token and
    # should only be allowed to access this specific project.
    project_scope: int | None = None
    token_name: str | None = None


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> AuthContext:
    if credentials:
        user = user_for_session_token(db, credentials.credentials)
        if user:
            return _build_context(user)

    if api_key:
        token_hash = ApiToken.hash(api_key)
        token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
        if token and not _is_token_expired(token):
            uid = token.user_id if token.user_id else token.created_by
            user = db.get(User, uid)
            if user and user.is_active and user.deleted_at is None:
                _record_token_use(db, token)
                return _build_context(user, project_scope=token.project_id, token_name=token.name)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def user_for_session_token(db: Session, token: str | None) -> User | None:
    claims = decode_token(token) if token else None
    if claims is None:
        return None
    user = (
        db.query(User)
        .filter(
            User.username == claims.subject,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
        .first()
    )
    return user if user and is_session_current(user, claims) else None


def get_current_user(ctx: AuthContext = Depends(get_auth_context)) -> User:
    return ctx.user


def require_project_access_ctx(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """Like require_project_access but returns the full AuthContext."""
    authorize_project(db, ctx, id)
    return ctx


def get_unscoped_user(ctx: AuthContext = Depends(get_auth_context)) -> User:
    """Account-level routes (admin, profile, personal tokens) must not be reachable
    with a project-scoped API token, even when its owner is an admin."""
    if ctx.project_scope is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project-scoped API tokens cannot access account-level routes",
        )
    return ctx.user


def require_admin(current: User = Depends(get_unscoped_user)) -> User:
    if not current.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current


def require_project_access(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
) -> User:
    """Returns the user only if the active credential can access the given project.
    Project-scoped API tokens may only access their own project. Non-admin users
    must be members of the project (directly or via a group). The path parameter
    must be named `id` (consistent with how project routes declare it)."""
    authorize_project(db, ctx, id)
    return ctx.user


def require_writable_project_access(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
) -> User:
    """Like require_project_access but also rejects mutations on archived projects."""
    user = require_project_access(id, db, ctx)
    project = db.get(Project, id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")
    return user


def require_project_writer(
    db: Session, user: User, project_id: int,
) -> None:
    """Raise 403 unless the user is admin, owner, or tester on the project."""
    if not is_project_writer(db, user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester role or higher required",
        )


def require_project_owner(db: Session, user: User, project_id: int) -> None:
    """Raise 403 unless the user is admin or owns the project, directly or through a group."""
    if user.is_admin or effective_role(db, user.id, project_id) == "owner":
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Project owner or admin required",
    )


def authorize_project(
    db: Session, ctx: AuthContext, project_id: int, roles: set[str] = VALID_ROLES,
) -> None:
    """Raise 403 unless the active credential may act on the project with one of
    `roles`. Flat routes (`/versions/{id}`, `/results/{id}`…) load the resource
    first and pass its `project_id` here."""
    _reject_out_of_scope_token(ctx, project_id)
    if ctx.user.is_admin:
        return
    role = effective_role(db, ctx.user.id, project_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a project member",
        )
    if role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient project role",
        )


def _build_context(
    user: User,
    project_scope: int | None = None,
    token_name: str | None = None,
) -> AuthContext:
    set_current_user_id(user.id)
    return AuthContext(user=user, project_scope=project_scope, token_name=token_name)


def _reject_out_of_scope_token(ctx: AuthContext, project_id: int) -> None:
    if ctx.project_scope is not None and ctx.project_scope != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token is not authorized for this project",
        )


def _is_token_expired(token: ApiToken) -> bool:
    if token.expires_at is None:
        return False
    return _as_utc(token.expires_at) <= datetime.now(UTC)


def _record_token_use(db: Session, token: ApiToken) -> None:
    now = datetime.now(UTC)
    if token.last_used_at is not None and now - _as_utc(token.last_used_at) < TOKEN_LAST_USED_RESOLUTION:
        return
    db.execute(update(ApiToken).where(ApiToken.id == token.id).values(last_used_at=now))
    db.commit()


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)
