from datetime import datetime
from urllib.parse import quote
from pydantic import BaseModel, Field, computed_field


class AttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str | None
    size_bytes: int | None
    uploaded_at: datetime
    uploaded_by: str | None
    file_path: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def url(self) -> str:
        path = self.file_path or ""
        relative = path.replace("/app/uploads", "", 1)
        segments = [quote(s, safe="") for s in relative.strip("/").split("/")]
        return "/files/" + "/".join(segments) if segments and segments[0] else ""

    model_config = {"from_attributes": True}


class TestStepBase(BaseModel):
    content: str
    expected_result: str | None = None
    order: int


class TestStepCreate(TestStepBase):
    pass


class TestStepUpdate(BaseModel):
    content: str | None = None
    expected_result: str | None = None
    order: int | None = None


class TestStepOut(TestStepBase):
    id: int
    test_case_id: int

    model_config = {"from_attributes": True}


class TestCaseBase(BaseModel):
    title: str
    description: str | None = None
    preconditions: str | None = None


class TestCaseCreate(TestCaseBase):
    suite_id: int


class TestCaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    preconditions: str | None = None
    suite_id: int | None = None


class TestCaseOut(TestCaseBase):
    id: int
    suite_id: int
    created_at: datetime
    updated_at: datetime
    steps: list[TestStepOut] = []
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class TestSuiteBase(BaseModel):
    title: str
    description: str | None = None
    parent_suite_id: int | None = None


class TestSuiteCreate(TestSuiteBase):
    pass


class TestSuiteUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    parent_suite_id: int | None = None


class TestSuiteOut(TestSuiteBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    child_suite_ids: list[int] = []
    test_case_ids: list[int] = []

    model_config = {"from_attributes": True}
