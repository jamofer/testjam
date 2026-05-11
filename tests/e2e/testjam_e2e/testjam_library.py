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
    NotificationsMixin,
    NotificationPreferencesMixin,
    SettingsMixin,
    StepResultsMixin,
    WebsocketMixin,
    AttachmentsMixin,
    BulkResultsMixin,
    ExportsMixin,
    MailpitMixin,
    UsersMixin,
    GroupsMixin,
    CaseTagsMixin,
    CaseStepReorderMixin,
    CaseRevisionsMixin,
    CaseSearchMixin,
    CleanupMixin,
    ListenerRunnerMixin,
    BrowserMixin,
    AuthUIMixin,
    ProjectsUIMixin,
    SuitesUIMixin,
    CasesUIMixin,
    PlansUIMixin,
    VersionsUIMixin,
    MembersUIMixin,
    ExecutionRunUIMixin,
    LiveUpdatesUIMixin,
    NotificationsUIMixin,
    ProfileUIMixin,
    SettingsUIMixin,
    CommandPaletteUIMixin,
    ResponsiveUIMixin,
    SuiteTreeUIMixin,
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
    NotificationsMixin,
    NotificationPreferencesMixin,
    SettingsMixin,
    StepResultsMixin,
    WebsocketMixin,
    AttachmentsMixin,
    BulkResultsMixin,
    ExportsMixin,
    MailpitMixin,
    UsersMixin,
    GroupsMixin,
    CaseTagsMixin,
    CaseStepReorderMixin,
    CaseRevisionsMixin,
    CaseSearchMixin,
    CleanupMixin,
    ListenerRunnerMixin,
    BrowserMixin,
    AuthUIMixin,
    ProjectsUIMixin,
    SuitesUIMixin,
    CasesUIMixin,
    PlansUIMixin,
    VersionsUIMixin,
    MembersUIMixin,
    ExecutionRunUIMixin,
    LiveUpdatesUIMixin,
    NotificationsUIMixin,
    ProfileUIMixin,
    SettingsUIMixin,
    CommandPaletteUIMixin,
    ResponsiveUIMixin,
    SuiteTreeUIMixin,
):
    """Robot Framework library for end-to-end testing of the Testjam API."""

    def __init__(self, base_url: str | None = None):
        url = base_url or os.getenv("TESTJAM_API_URL", "http://localhost:8000/api/v1")
        self.base_url = url
        self.client = HttpClient(url)
        self.mailpit_url = os.getenv("TESTJAM_MAILPIT_URL", "http://localhost:8025").rstrip("/")

        self.current_project_id: int | None = None
        self.current_version_id: int | None = None
        self.current_suite_id: int | None = None
        self.current_case_id: int | None = None
        self.current_plan_id: int | None = None
        self.current_execution_id: int | None = None
        self.current_result_id: int | None = None
        self.current_step_id: int | None = None
        self.current_step_result_id: int | None = None
        self.current_group_id: int | None = None
        self.last_status_code: int | None = None
        self.last_import_summary: dict | None = None
        self.websocket = None
        self.last_websocket_frame: dict | None = None
        self.last_bulk_response: dict | None = None
        self.last_download: dict | None = None
        self.last_case_search: list | None = None
        self.listener_project_name: str | None = None
        self.frontend_url: str = os.getenv("TESTJAM_FRONTEND_URL", "http://localhost:5173").rstrip("/")
