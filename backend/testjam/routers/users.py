from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_admin
from testjam.auth.security import hash_password, verify_password
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.user import (
    AdminUserUpdate,
    PasswordChange,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserActivity,
    UserCreate,
    UserDeleteRequest,
    UserOut,
    UserUpdate,
)
from testjam.services.admin_reset import issue_temporary_password, send_reset_email
from testjam.services.settings import get_settings as get_app_settings
from testjam.services.user_activity import collect_user_activity
from testjam.services.user_lifecycle import soft_delete_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserOut])
def list_users(
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    query = db.query(User)
    if include_deleted and not current.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required to view deleted users")
    if not include_deleted:
        query = query.filter(User.deleted_at.is_(None))
    return query.all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(**body.model_dump(exclude={"password"}), hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current


@router.put("/me", response_model=UserOut)
def update_me(body: UserUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current, field, value)
    db.commit()
    db.refresh(current)
    return current


@router.put("/me/password", status_code=204)
def change_my_password(body: PasswordChange, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not verify_password(body.current_password, current.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current.hashed_password = hash_password(body.new_password)
    db.commit()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    body: UserDeleteRequest = Body(default_factory=UserDeleteRequest),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not get_app_settings(db).allow_user_self_delete:
        raise HTTPException(status_code=403, detail="Self-account deletion is disabled by the administrator")
    soft_delete_user(db, current, body.owned_projects)


@router.get("/by-username/{username}", response_model=UserOut)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    if user.deleted_at is not None and not current.is_admin:
        raise HTTPException(status_code=404, detail="Not found")
    return user


@router.get("/{id}", response_model=UserOut)
def get_user(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    if user.deleted_at is not None and not current.is_admin:
        raise HTTPException(status_code=404, detail="Not found")
    return user


@router.put("/{id}", response_model=UserOut)
def update_user(id: int, body: AdminUserUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    payload = body.model_dump(exclude_none=True)
    new_username = payload.get("username")
    if new_username and new_username != user.username:
        clash = db.query(User).filter(User.username == new_username, User.id != id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Username already exists")
    if payload.pop("clear_lockout", False):
        user.locked_until = None
        user.failed_login_count = 0
    if "password" in payload:
        user.hashed_password = hash_password(payload.pop("password"))
    for field, value in payload.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{id}/reset-password", response_model=ResetPasswordResponse)
def admin_reset_password(
    id: int,
    body: ResetPasswordRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.get(User, id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if body.mode == "temporary_password":
        temporary = issue_temporary_password(db, user)
        return ResetPasswordResponse(mode="temporary_password", temporary_password=temporary)
    send_reset_email(db, user, background)
    return ResetPasswordResponse(mode="email")


@router.get("/{id}/activity", response_model=UserActivity)
def get_user_activity(id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return collect_user_activity(db, user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int,
    body: UserDeleteRequest = Body(default_factory=UserDeleteRequest),
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    user = db.get(User, id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="Admins cannot delete their own account")
    soft_delete_user(db, user, body.owned_projects)


@router.post("/{id}/restore", response_model=UserOut)
def restore_user(id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, id)
    if not user or user.deleted_at is None:
        raise HTTPException(status_code=404, detail="Not found")
    user.deleted_at = None
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user
