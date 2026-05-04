from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from testjam.auth.dependencies import get_current_user
from testjam.database import get_db
from testjam.models.execution import TestExecution
from testjam.models.project import Project, ProjectMember
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_out(project: Project, db: Session) -> ProjectOut:
    suite_count = db.query(func.count(TestSuite.id)).filter(TestSuite.project_id == project.id).scalar() or 0
    case_count = (
        db.query(func.count(TestCase.id))
        .join(TestSuite, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id == project.id)
        .scalar() or 0
    )
    execution_count = (
        db.query(func.count(TestExecution.id)).filter(TestExecution.project_id == project.id).scalar() or 0
    )
    last_execution_at = (
        db.query(func.max(TestExecution.created_at)).filter(TestExecution.project_id == project.id).scalar()
    )
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        suite_count=suite_count,
        case_count=case_count,
        execution_count=execution_count,
        last_execution_at=last_execution_at,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    member_project_ids = db.query(ProjectMember.project_id).filter(ProjectMember.user_id == current.id)
    projects = db.query(Project).filter(Project.id.in_(member_project_ids)).all()
    return [_project_out(p, db) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    project = Project(**body.model_dump())
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current.id, role="owner"))
    db.commit()
    db.refresh(project)
    return _project_out(project, db)


@router.get("/{id}", response_model=ProjectOut)
def get_project(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    return _project_out(project, db)


@router.put("/{id}", response_model=ProjectOut)
def update_project(id: int, body: ProjectUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _project_out(project, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(project)
    db.commit()
