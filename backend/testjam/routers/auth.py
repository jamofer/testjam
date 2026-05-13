from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from testjam.auth.lockout import (
    clear_lockout,
    is_locked,
    register_failed_attempt,
    seconds_until_unlock,
)
from testjam.auth.security import create_access_token, verify_password
from testjam.core.config import settings
from testjam.core.rate_limit import LOGIN_RATE_LIMIT, limiter
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.user import TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if user and is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account locked due to too many failed login attempts",
            headers={"Retry-After": str(seconds_until_unlock(user))},
        )
    if not user or not verify_password(form.password, user.hashed_password):
        if user:
            register_failed_attempt(db, user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    clear_lockout(db, user)
    token = create_access_token(subject=user.username)
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
