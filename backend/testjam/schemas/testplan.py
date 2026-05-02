from datetime import datetime
from pydantic import BaseModel


class TestPlanCreate(BaseModel):
    title: str
    description: str | None = None
    test_case_ids: list[int] = []


class TestPlanUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    test_case_ids: list[int] | None = None


class TestPlanOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    test_case_ids: list[int] = []

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        instance.test_case_ids = [c.id for c in obj.cases]
        return instance
