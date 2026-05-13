from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user, require_admin
from testjam.auth.security import hash_password, verify_password
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.user import (
    PasswordChange,
    UserCreate,
    UserDeleteRequest,
    UserOut,
    UserUpdate,
)
from testjam.services.settings import get_settings as get_app_settings
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


@router.get("/{id}", response_model=UserOut)
def get_user(id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    if user.deleted_at is not None and not current.is_admin:
        raise HTTPException(status_code=404, detail="Not found")
    return user


@router.put("/{id}", response_model=UserOut)
def update_user(id: int, body: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    payload = body.model_dump(exclude_none=True)
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
