from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from testjam.core.config import settings
from testjam.schemas.user import UserOut


class AttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str | None
    size_bytes: int | None
    uploaded_at: datetime
    uploaded_by: str | None
    result_id: int | None = Field(default=None, exclude=True)
    test_case_id: int | None = Field(default=None, exclude=True)
    file_path: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def url(self) -> str:
        if self.result_id is not None:
            return f"{settings.API_V1_PREFIX}/results/{self.result_id}/attachments/{self.id}/download"
        if self.test_case_id is not None:
            return f"{settings.API_V1_PREFIX}/cases/{self.test_case_id}/attachments/{self.id}/download"
        return ""

    model_config = {"from_attributes": True}


class TestStepBase(BaseModel):
    action: str
    expected_result: str | None = None
    order: int | None = None
    step_type: str = "action"


class TestStepCreate(TestStepBase):
    pass


class TestStepUpdate(BaseModel):
    action: str | None = None
    expected_result: str | None = None
    order: int | None = None
    step_type: str | None = None


class TestStepOut(TestStepBase):
    id: int
    test_case_id: int

    model_config = {"from_attributes": True}


class TestCaseBase(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = []
    preconditions: str | None = None
    setup: str | None = None
    teardown: str | None = None
    external_id: str | None = None


class TestCaseCreate(TestCaseBase):
    suite_id: int


class TestCaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    preconditions: str | None = None
    setup: str | None = None
    teardown: str | None = None
    external_id: str | None = None
    suite_id: int | None = None


class UserMini(BaseModel):
    id: int
    username: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class TestCaseOut(TestCaseBase):
    id: int
    suite_id: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    created_by: UserMini | None = None
    updated_by: UserMini | None = None
    steps: list[TestStepOut] = []
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class SuiteStepCreate(BaseModel):
    action: str
    step_type: str  # "setup" | "teardown"
    order: int


class SuiteStepUpdate(BaseModel):
    action: str | None = None
    order: int | None = None


class SuiteStepOut(BaseModel):
    id: int
    suite_id: int
    step_type: str
    action: str
    order: int

    model_config = {"from_attributes": True}


class TestSuiteBase(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = []
    parent_suite_id: int | None = None


class TestSuiteCreate(TestSuiteBase):
    pass


class TestSuiteUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    parent_suite_id: int | None = None


class TestSuiteOut(TestSuiteBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    child_suite_ids: list[int] = []
    test_case_ids: list[int] = []
    steps: list[SuiteStepOut] = []

    model_config = {"from_attributes": True}


class SuiteDeleteImpact(BaseModel):
    suite_count: int
    case_count: int
    result_count: int
    execution_count: int


class SuiteArchiveResult(BaseModel):
    suite_count: int
    archived_case_count: int


class CaseCommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CaseCommentUpdate(BaseModel):
    body: str = Field(min_length=1)


class CaseCommentOut(BaseModel):
    id: int
    test_case_id: int
    body: str
    created_by: UserOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
