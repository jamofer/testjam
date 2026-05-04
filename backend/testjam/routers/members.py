from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_project_access
from testjam.database import get_db
from testjam.models.project import Project, ProjectMember
from testjam.models.user import User
from testjam.schemas.members import ProjectMemberAdd, ProjectMemberOut, ProjectMemberUpdate, VALID_ROLES

router = APIRouter(prefix="/projects/{id}/members", tags=["Members"])


def _out(m: ProjectMember) -> ProjectMemberOut:
    return ProjectMemberOut(
        id=m.id,
        user_id=m.user_id,
        username=m.user.username,
        full_name=m.user.full_name,
        role=m.role,
        added_at=m.added_at,
    )


def _require_owner(project: Project, current: User, db: Session) -> None:
    if current.is_admin:
        return
    m = db.query(ProjectMember).filter_by(project_id=project.id, user_id=current.id).first()
    if not m or m.role != "owner":
        raise HTTPException(status_code=403, detail="Project owner or admin required")


@router.get("", response_model=list[ProjectMemberOut])
def list_members(id: int, db: Session = Depends(get_db), _: User = Depends(require_project_access)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return [_out(m) for m in project.members]


@router.post("", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    id: int,
    body: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")
    user = db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.query(ProjectMember).filter_by(project_id=id, user_id=body.user_id).first():
        raise HTTPException(status_code=409, detail="User is already a member")
    m = ProjectMember(project_id=id, user_id=body.user_id, role=body.role)
    db.add(m)
    db.commit()
    db.refresh(m)
    return _out(m)


@router.put("/{user_id}", response_model=ProjectMemberOut)
def update_member(
    id: int,
    user_id: int,
    body: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")
    m = db.query(ProjectMember).filter_by(project_id=id, user_id=user_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    m.role = body.role
    db.commit()
    db.refresh(m)
    return _out(m)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _require_owner(project, current, db)
    m = db.query(ProjectMember).filter_by(project_id=id, user_id=user_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(m)
    db.commit()
