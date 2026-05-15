from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from testjam.models.project import Project, ProjectMember
from testjam.models.user import User


def transfer_ownership(db: Session, project: Project, new_owner_id: int) -> None:
    new_owner = db.get(User, new_owner_id)
    if new_owner is None or new_owner.deleted_at is not None or not new_owner.is_active:
        raise HTTPException(status_code=400, detail="New owner is not a valid active user")

    current_owner_membership = (
        db.query(ProjectMember)
        .filter_by(project_id=project.id, role="owner")
        .first()
    )
    new_owner_membership = (
        db.query(ProjectMember)
        .filter_by(project_id=project.id, user_id=new_owner_id)
        .first()
    )

    if current_owner_membership and current_owner_membership.user_id == new_owner_id:
        return

    if new_owner_membership is None:
        new_owner_membership = ProjectMember(
            project_id=project.id, user_id=new_owner_id, role="owner",
        )
        db.add(new_owner_membership)
    else:
        new_owner_membership.role = "owner"

    if current_owner_membership and current_owner_membership.user_id != new_owner_id:
        current_owner_membership.role = "editor"

    db.commit()
