from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


VERSIONS_HEADING = 'h1:has-text("Versions")'
VERSION_NAME_INPUT = 'input[placeholder="Version name (e.g. 1.4.0, sprint-23)…"]'
VERSION_TAG_INPUT = 'input[placeholder="VCS tag (optional)"]'
VERSION_ADD_BUTTON = 'button[type="submit"]:has-text("Add")'


def _version_row(name: str) -> str:
    return f'li:has(span:text-is("{name}"))'


def _version_delete(name: str) -> str:
    return f'{_version_row(name)} button:last-child'


def _version_status_toggle(name: str) -> str:
    return f'{_version_row(name)} button[title="Click to change status"]'


def _version_status_label(name: str, label: str) -> str:
    return f'{_version_row(name)}:has-text("{label}")'


class VersionsUIMixin:
    """Browser keywords driving the Versions page."""

    @keyword("I open the versions page")
    def open_versions(self) -> None:
        assert self.current_project_id is not None, "No current project set"
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/projects/{self.current_project_id}/versions",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State", VERSIONS_HEADING, "visible", "timeout=5s",
        )

    @keyword("I create a version via the UI named ${name}")
    def create_version_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Fill Text", VERSION_NAME_INPUT, name)
        BuiltIn().run_keyword("Click", VERSION_ADD_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", _version_row(name), "visible", "timeout=5s",
        )

    @keyword("I create a version via the UI named ${name} tagged ${tag}")
    def create_version_ui_with_tag(self, name: str, tag: str) -> None:
        BuiltIn().run_keyword("Fill Text", VERSION_NAME_INPUT, name)
        BuiltIn().run_keyword("Fill Text", VERSION_TAG_INPUT, tag)
        BuiltIn().run_keyword("Click", VERSION_ADD_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", _version_row(name), "visible", "timeout=5s",
        )

    @keyword("I delete the version ${name} via the UI")
    def delete_version_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _version_delete(name))
        BuiltIn().run_keyword(
            "Wait For Elements State", _version_row(name), "hidden", "timeout=5s",
        )

    @keyword("I cycle the status of version ${name}")
    def cycle_version_status(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _version_status_toggle(name))

    @keyword("the versions list should contain ${name}")
    def versions_should_contain(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _version_row(name), "visible", "timeout=5s",
        )

    @keyword("the versions list should not contain ${name}")
    def versions_should_not_contain(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _version_row(name), "hidden", "timeout=5s",
        )

    @keyword("the version ${name} should be in ${status} state")
    def version_status_should_be_ui(self, name: str, status: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            _version_status_label(name, status.capitalize()),
            "visible", "timeout=5s",
        )

    @keyword("the version ${name} should have tag ${tag}")
    def version_tag_should_be(self, name: str, tag: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{_version_row(name)} >> text={tag}', "visible", "timeout=5s",
        )
