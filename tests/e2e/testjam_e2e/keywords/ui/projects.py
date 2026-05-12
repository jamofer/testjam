from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


NEW_PROJECT_INPUT = 'input[placeholder="New project name…"]'
SEARCH_INPUT = 'input[placeholder="Search projects…"]'
CREATE_BUTTON = 'button[type="submit"]:has-text("Create")'
PROJECTS_HEADING = 'h1:has-text("Projects")'
DELETE_BUTTON = 'button[title="Delete project"]'
LIST_LOADING = '[role="status"][aria-busy="true"]'


def _project_link(name: str) -> str:
    return f'li a:has-text("{name}")'


def _project_item(name: str) -> str:
    return f'li:has(a:has-text("{name}"))'


class ProjectsUIMixin:
    """Browser keywords driving the Projects page."""

    @keyword("I open the projects page")
    def open_projects_page(self) -> None:
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/projects")
        BuiltIn().run_keyword(
            "Wait For Elements State", PROJECTS_HEADING, "visible", "timeout=10s",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State", LIST_LOADING, "detached", "timeout=30s",
        )

    @keyword("the UI projects whose name starts with ${prefix} are purged")
    def purge_projects_by_prefix(self, prefix: str) -> None:
        self.authenticate_as_admin()
        for project in self.client.get("/projects").json():
            if project["name"].startswith(prefix):
                self.client.delete(f"/projects/{project['id']}")

    @keyword("the projects page is fresh with no ${prefix} projects")
    def fresh_projects_page(self, prefix: str) -> None:
        self.purge_projects_by_prefix(prefix)
        self.open_projects_page()

    @keyword("I create a project via the UI named ${name}")
    def create_project_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Fill Text", NEW_PROJECT_INPUT, name)
        BuiltIn().run_keyword("Press Keys", NEW_PROJECT_INPUT, "Enter")
        BuiltIn().run_keyword(
            "Wait For Elements State", _project_link(name), "visible", "timeout=30s",
        )

    @keyword("I search projects for ${query}")
    def search_projects(self, query: str) -> None:
        BuiltIn().run_keyword("Fill Text", SEARCH_INPUT, query)

    @keyword("I open the project ${name}")
    def open_project(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _project_link(name))
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'h1:has-text("{name}")', "visible", "timeout=10s",
        )

    @keyword("I delete the project ${name} via the UI")
    def delete_project_ui(self, name: str) -> None:
        selector = f'{_project_item(name)} >> {DELETE_BUTTON}'
        BuiltIn().run_keyword("Click", selector)
        BuiltIn().run_keyword(
            "Wait For Elements State", _project_link(name), "hidden", "timeout=10s",
        )

    @keyword("the projects list should contain ${name}")
    def projects_should_contain(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _project_link(name), "visible", "timeout=10s",
        )

    @keyword("the projects list should not contain ${name}")
    def projects_should_not_contain(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _project_link(name), "hidden", "timeout=10s",
        )
