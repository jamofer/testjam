from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_project_access
from testjam.database import get_db
from testjam.models.project import Project, ProjectGroup
from testjam.models.user import Group, GroupMember, User
from testjam.schemas.project import (
    ProjectGroupAssignmentAdd,
    ProjectGroupAssignmentOut,
    ProjectGroupAssignmentUpdate,
)
from testjam.services.permissions import VALID_ROLES, effective_role

router = APIRouter(prefix="/projects/{id}/groups", tags=["Project Groups"])


def _require_owner_or_admin(project: Project, current: User, db: Session) -> None:
    if current.is_admin:
        return
    if effective_role(db, current.id, project.id) == "owner":
        return
    raise HTTPException(status_code=403, detail="Project owner or admin required")


def _to_out(assignment: ProjectGroup, member_count: int) -> ProjectGroupAssignmentOut:
    return ProjectGroupAssignmentOut(
        id=assignment.id,
        group_id=assignment.group_id,
        group_name=assignment.group.name,
        role=assignment.role,
        member_count=member_count,
        added_at=assignment.added_at,
    )


def _member_counts(db: Session, group_ids: list[int]) -> dict[int, int]:
    if not group_ids:
        return {}
    rows = (
        db.query(GroupMember.group_id, func.count(GroupMember.id))
        .filter(GroupMember.group_id.in_(group_ids))
        .group_by(GroupMember.group_id)
        .all()
    )
    return dict(rows)


def _validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}",
        )


def _load_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectGroupAssignmentOut])
def list_project_groups(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    project = _load_project(db, id)
    assignments = project.group_assignments
    counts = _member_counts(db, [a.group_id for a in assignments])
    return [_to_out(assignment, counts.get(assignment.group_id, 0)) for assignment in assignments]


@router.post("", response_model=ProjectGroupAssignmentOut, status_code=status.HTTP_201_CREATED)
def add_project_group(
    id: int,
    body: ProjectGroupAssignmentAdd,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = _load_project(db, id)
    _require_owner_or_admin(project, current, db)
    _validate_role(body.role)
    if not db.get(Group, body.group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    if db.query(ProjectGroup).filter_by(project_id=id, group_id=body.group_id).first():
        raise HTTPException(status_code=409, detail="Group already assigned to this project")
    assignment = ProjectGroup(project_id=id, group_id=body.group_id, role=body.role)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return _to_out(assignment, _member_counts(db, [assignment.group_id]).get(assignment.group_id, 0))


@router.put("/{group_id}", response_model=ProjectGroupAssignmentOut)
def update_project_group(
    id: int,
    group_id: int,
    body: ProjectGroupAssignmentUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = _load_project(db, id)
    _require_owner_or_admin(project, current, db)
    _validate_role(body.role)
    assignment = db.query(ProjectGroup).filter_by(project_id=id, group_id=group_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Group is not assigned to this project")
    assignment.role = body.role
    db.commit()
    db.refresh(assignment)
    return _to_out(assignment, _member_counts(db, [group_id]).get(group_id, 0))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_group(
    id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = _load_project(db, id)
    _require_owner_or_admin(project, current, db)
    assignment = db.query(ProjectGroup).filter_by(project_id=id, group_id=group_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Group is not assigned to this project")
    db.delete(assignment)
    db.commit()
