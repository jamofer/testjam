from datetime import datetime
from pydantic import BaseModel


class ApiTokenCreate(BaseModel):
    name: str
    expires_at: datetime | None = None


class ApiTokenOut(BaseModel):
    id: int
    name: str
    prefix: str
    user_id: int | None
    project_id: int | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ApiTokenCreated(ApiTokenOut):
    token: str
