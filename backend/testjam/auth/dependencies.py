from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.orm import Session

from testjam.auth.security import decode_token
from testjam.database import get_db
from testjam.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    username = None

    if credentials:
        username = decode_token(credentials.credentials)
    elif api_key:
        # API keys stored as hashed tokens associated to a user — simplified lookup by raw key for now
        user = db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
        if user:
            return user

    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user
