from datetime import datetime
from pydantic import BaseModel, ConfigDict

from testjam.schemas.testcase import UserMini


class CaseRevisionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    change_kind: str
    actor: UserMini | None = None
    created_at: datetime


class CaseRevisionDetail(CaseRevisionSummary):
    snapshot: dict
