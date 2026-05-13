from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
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
from testjam.services.password_reset import confirm_password_reset, request_password_reset

router = APIRouter(prefix="/auth", tags=["Auth"])

MIN_PASSWORD_LENGTH = 8


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH)


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


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(LOGIN_RATE_LIMIT)
def password_reset_request(
    request: Request,
    body: PasswordResetRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    request_password_reset(db, body.email, background=background)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    succeeded = confirm_password_reset(db, body.token, body.new_password)
    if not succeeded:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
