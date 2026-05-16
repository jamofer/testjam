from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


NEW_SUITE_TRIGGER = 'button:has-text("New suite")'
SUITE_DIALOG_INPUT = 'input[placeholder="Suite name…"]'
SUITE_DIALOG_SUBMIT = 'button:has-text("Create suite")'


def _suite_name_span(name: str) -> str:
    return f'span.truncate:text-is("{name}")'


def _suite_header(name: str) -> str:
    return f'div.cursor-pointer:has({_suite_name_span(name)})'


def _suite_delete(name: str) -> str:
    return f'{_suite_header(name)} button:last-child'


def _suite_add_case(name: str) -> str:
    return f'{_suite_header(name)} button:has-text("Case")'


class SuitesUIMixin:
    """Browser keywords driving the suite list inside a project."""

    @keyword("I open the project detail page for ${name}")
    def open_project_detail(self, name: str) -> None:
        project = self._find_project_id_by_name(name)
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/projects/{project}")
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'h1:has-text("{name}")', "visible", "timeout=10s",
        )

    @keyword("I have a fresh project named ${name}")
    def have_fresh_project(self, name: str) -> None:
        self.authenticate_as_admin()
        for project in self.client.get("/projects").json():
            if project["name"] == name:
                self.client.delete(f"/projects/{project['id']}")
        created = self.client.post("/projects", json={"name": name}).json()
        self.current_project_id = created["id"]
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/projects/{created['id']}/cases")
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'h1:has-text("{name}")', "visible", "timeout=10s",
        )

    @keyword("I create a suite via the UI named ${name}")
    def create_suite_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Click", NEW_SUITE_TRIGGER)
        BuiltIn().run_keyword(
            "Wait For Elements State", SUITE_DIALOG_INPUT, "visible", "timeout=5s",
        )
        BuiltIn().run_keyword("Fill Text", SUITE_DIALOG_INPUT, name)
        BuiltIn().run_keyword("Click", SUITE_DIALOG_SUBMIT)
        BuiltIn().run_keyword(
            "Wait For Elements State", _suite_header(name), "visible", "timeout=10s",
        )

    @keyword("I delete the suite ${name} via the UI")
    def delete_suite_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _suite_delete(name))
        BuiltIn().run_keyword(
            "Wait For Elements State", _suite_header(name), "hidden", "timeout=5s",
        )

    @keyword("I expand the suite ${name}")
    def expand_suite(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _suite_name_span(name))

    @keyword("the project should list the suite ${name}")
    def project_should_list_suite(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _suite_header(name), "visible", "timeout=10s",
        )

    @keyword("the project should not list the suite ${name}")
    def project_should_not_list_suite(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _suite_header(name), "hidden", "timeout=10s",
        )

    def _find_project_id_by_name(self, name: str) -> int:
        for project in self.client.get("/projects").json():
            if project["name"] == name:
                return project["id"]
        raise AssertionError(f"Project '{name}' not found")
