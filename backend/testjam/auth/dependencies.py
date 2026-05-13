from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.orm import Session

from testjam.auth.security import decode_token
from testjam.core.logging import set_current_user_id
from testjam.database import get_db
from testjam.models.project import Project
from testjam.models.token import ApiToken
from testjam.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


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
        username = decode_token(credentials.credentials)
        if username:
            user = (
                db.query(User)
                .filter(
                    User.username == username,
                    User.is_active == True,
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if user:
                return _build_context(user)

    if api_key:
        token_hash = ApiToken.hash(api_key)
        token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
        if token and not _is_token_expired(token):
            token.last_used_at = datetime.now(timezone.utc)
            db.commit()
            uid = token.user_id if token.user_id else token.created_by
            user = db.get(User, uid)
            if user and user.is_active and user.deleted_at is None:
                return _build_context(user, project_scope=token.project_id, token_name=token.name)
        # Fallback: legacy api_key field on User
        user = (
            db.query(User)
            .filter(
                User.api_key == api_key,
                User.is_active == True,
                User.deleted_at.is_(None),
            )
            .first()
        )
        if user:
            return _build_context(user)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_current_user(ctx: AuthContext = Depends(get_auth_context)) -> User:
    return ctx.user


def require_project_access_ctx(id: int, ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """Like require_project_access but returns the full AuthContext."""
    if ctx.project_scope is not None and ctx.project_scope != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token is not authorized for this project",
        )
    return ctx


def require_admin(current: User = Depends(get_current_user)) -> User:
    if not current.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current


def require_project_access(id: int, ctx: AuthContext = Depends(get_auth_context)) -> User:
    """Returns the user only if the active credential can access the given project.
    Project-scoped API tokens may only access their own project. The path parameter
    must be named `id` (consistent with how project routes declare it)."""
    if ctx.project_scope is not None and ctx.project_scope != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token is not authorized for this project",
        )
    return ctx.user


def require_writable_project_access(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
) -> User:
    """Like require_project_access but also rejects mutations on archived projects."""
    user = require_project_access(id, ctx)
    project = db.get(Project, id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")
    return user


def _build_context(
    user: User,
    project_scope: int | None = None,
    token_name: str | None = None,
) -> AuthContext:
    set_current_user_id(user.id)
    return AuthContext(user=user, project_scope=project_scope, token_name=token_name)


def _is_token_expired(token: ApiToken) -> bool:
    if token.expires_at is None:
        return False
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)
