from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from testjam.auth.dependencies import require_admin
from testjam.database import get_db
from testjam.models.user import User
from testjam.schemas.project import AdminProjectRow
from testjam.services.admin_projects import list_admin_projects

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/projects", response_model=list[AdminProjectRow])
def admin_list_projects(
    include_archived: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_admin_projects(db, include_archived=include_archived)
