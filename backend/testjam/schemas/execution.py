from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from urllib.parse import quote
from testjam.core.config import settings
from testjam.schemas.testcase import AttachmentOut
from testjam.schemas.user import UserOut


class ExecutionAttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str | None
    size_bytes: int | None
    uploaded_at: datetime
    file_path: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def url(self) -> str:
        path = self.file_path or ""
        relative = path.replace(settings.UPLOAD_DIR, "", 1)
        segments = [quote(s, safe="") for s in relative.strip("/").split("/")]
        return "/files/" + "/".join(segments) if segments and segments[0] else ""

    model_config = {"from_attributes": True}


class TestStepResultCreate(BaseModel):
    step_id: int
    status: str
    comment: str | None = None
    log_output: str | None = None
    duration_ms: int | None = None


class TestStepResultUpdate(BaseModel):
    status: str | None = None
    comment: str | None = None
    log_output: str | None = None
    duration_ms: int | None = None


class TestStepResultOut(BaseModel):
    id: int
    test_result_id: int
    step_id: int
    status: str
    comment: str | None
    duration_ms: int | None = None
    log_output: str | None = None

    model_config = {"from_attributes": True}


class TestResultCreate(BaseModel):
    test_case_id: int
    status: str = "not_run"
    comment: str | None = None
    executed_by: str | None = None
    executed_at: datetime | None = None
    duration_ms: int | None = None
    step_results: list[TestStepResultCreate] = []


class TestResultUpdate(BaseModel):
    status: str | None = None
    comment: str | None = None
    executed_by: str | None = None
    executed_at: datetime | None = None
    duration_ms: int | None = None


class TestResultOut(BaseModel):
    id: int
    execution_id: int
    test_case_id: int
    test_case_title: str | None = None
    status: str
    comment: str | None
    executed_by: str | None
    executed_at: datetime | None
    duration_ms: int | None
    step_results: list[TestStepResultOut] = []
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class BulkResultItem(TestResultCreate):
    pass


class BulkResultCreate(BaseModel):
    results: list[BulkResultItem]


class BulkResultResponse(BaseModel):
    created: int
    updated: int
    errors: list[dict] = []


class ExecutionSummary(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    not_run: int = 0


class TestExecutionCreate(BaseModel):
    title: str
    description: str | None = None
    type: str
    version: str | None = None
    version_id: int | None = None
    environment: str | None = None
    assigned_to_id: int | None = None
    triggered_by: str | None = None
    test_case_ids: list[int] = []


class TestExecutionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    version: str | None = None
    version_id: int | None = None
    environment: str | None = None
    assigned_to_id: int | None = None
    finished_at: datetime | None = None


class TestExecutionOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    type: str
    status: str
    version: str | None
    version_id: int | None = None
    environment: str | None
    assigned_to: UserOut | None = None
    created_by: UserOut | None = None
    token_name: str | None = None
    triggered_by: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    summary: ExecutionSummary = ExecutionSummary()
    attachments: list[ExecutionAttachmentOut] = []

    model_config = {"from_attributes": True}
