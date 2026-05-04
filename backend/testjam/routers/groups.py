from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.user import Group, GroupMember, User
from testjam.schemas.user import GroupCreate, GroupMemberOut, GroupMemberUpdate, GroupOut

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Group).all()


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(body: GroupCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Group).filter(Group.name == body.name).first():
        raise HTTPException(status_code=400, detail="Group name already exists")
    group = Group(**body.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("/{id}", response_model=GroupOut)
def get_group(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    group = db.get(Group, id)
    if not group:
        raise HTTPException(status_code=404, detail="Not found")
    return group


@router.put("/{id}", response_model=GroupOut)
def update_group(id: int, body: GroupCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    group = db.get(Group, id)
    if not group:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(group, field, value)
    db.commit()
    db.refresh(group)
    return group


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    group = db.get(Group, id)
    if not group:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(group)
    db.commit()


def _member_out(m: GroupMember) -> GroupMemberOut:
    return GroupMemberOut(user_id=m.user_id, username=m.user.username, role=m.role)


@router.get("/{id}/members", response_model=list[GroupMemberOut])
def list_members(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    group = db.get(Group, id)
    if not group:
        raise HTTPException(status_code=404, detail="Not found")
    return [_member_out(m) for m in group.members]


@router.post("/{id}/members", status_code=status.HTTP_201_CREATED)
def add_member(id: int, user_id: int, role: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(Group, id):
        raise HTTPException(status_code=404, detail="Group not found")
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(GroupMember).filter_by(group_id=id, user_id=user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in group")
    db.add(GroupMember(group_id=id, user_id=user_id, role=role))
    db.commit()


@router.put("/{id}/members/{user_id}")
def update_member(id: int, user_id: int, body: GroupMemberUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter_by(group_id=id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = body.role
    db.commit()
    return {"ok": True}


@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(id: int, user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter_by(group_id=id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
