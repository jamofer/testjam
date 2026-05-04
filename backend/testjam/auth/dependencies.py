from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.orm import Session

from testjam.auth.security import decode_token
from testjam.database import get_db
from testjam.models.token import ApiToken
from testjam.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    if credentials:
        username = decode_token(credentials.credentials)
        if username:
            user = db.query(User).filter(User.username == username, User.is_active == True).first()
            if user:
                return user

    if api_key:
        token_hash = ApiToken.hash(api_key)
        token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
        if token:
            token.last_used_at = datetime.now(timezone.utc)
            db.commit()
            uid = token.user_id if token.user_id else token.created_by
            user = db.get(User, uid)
            if user and user.is_active:
                return user
        # Fallback: legacy api_key field on User
        user = db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
        if user:
            return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
