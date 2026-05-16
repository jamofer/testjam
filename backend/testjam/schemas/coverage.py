from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from testjam.schemas.version import ProjectVersionOut


class CoverageCase(BaseModel):
    id: int
    name: str
    suite_id: int
    suite_name: str


class CoverageCell(BaseModel):
    case_id: int
    version_id: int
    status: str
    last_run_at: datetime | None
    execution_id: int | None


class CoverageMatrix(BaseModel):
    versions: list[ProjectVersionOut]
    cases: list[CoverageCase]
    cells: list[CoverageCell]
