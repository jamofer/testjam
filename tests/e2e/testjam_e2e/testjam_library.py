import os

from robot.api.deco import library

from testjam_e2e.client import HttpClient
from testjam_e2e.keywords import (
    AuthMixin,
    ProjectMixin,
    VersionMixin,
    SuiteMixin,
    CaseMixin,
    PlanMixin,
    ExecutionMixin,
    ImportMixin,
    MembersMixin,
    TokensMixin,
)


@library(scope="TEST", auto_keywords=False)
class TestjamLibrary(
    AuthMixin,
    ProjectMixin,
    VersionMixin,
    SuiteMixin,
    CaseMixin,
    PlanMixin,
    ExecutionMixin,
    ImportMixin,
    MembersMixin,
    TokensMixin,
):
    """Robot Framework library for end-to-end testing of the Testjam API."""

    def __init__(self, base_url: str | None = None):
        url = base_url or os.getenv("TESTJAM_BASE_URL", "http://localhost:8000/api/v1")
        self.client = HttpClient(url)

        self.current_project_id: int | None = None
        self.current_version_id: int | None = None
        self.current_suite_id: int | None = None
        self.current_case_id: int | None = None
        self.current_plan_id: int | None = None
        self.current_execution_id: int | None = None
        self.last_status_code: int | None = None
        self.last_import_summary: dict | None = None
