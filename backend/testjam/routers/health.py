from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from testjam.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict:
    db_status = _ping_database(db)
    if db_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "version": _app_version(), "db": db_status}
    return {"status": "ok", "version": _app_version(), "db": db_status}


def _ping_database(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except SQLAlchemyError:
        return "down"


def _app_version() -> str:
    try:
        return version("testjam-api")
    except PackageNotFoundError:
        return "unknown"
