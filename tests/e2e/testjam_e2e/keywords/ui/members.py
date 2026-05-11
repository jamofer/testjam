from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


MEMBERS_HEADING = 'h1:has-text("Members & Access")'
MEMBERS_SECTION = 'section:has(h2:has-text("Members"))'
ADD_FORM = 'form:has(select)'
USER_SELECT = f'{ADD_FORM} >> select >> nth=0'
ROLE_SELECT = f'{ADD_FORM} >> select >> nth=1'
ADD_BUTTON = f'{ADD_FORM} >> button:has-text("Add")'


def _member_row(username: str) -> str:
    return f'div.flex.items-center.gap-3:has(p:text-is("@{username}"))'


def _member_remove(username: str) -> str:
    return f'{_member_row(username)} button:last-child'


def _member_role_select(username: str) -> str:
    return f'{_member_row(username)} select'


class MembersUIMixin:
    """Browser keywords driving the project Members page."""

    @keyword("I open the members page")
    def open_members(self) -> None:
        assert self.current_project_id is not None, "No current project set"
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/projects/{self.current_project_id}/members",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State", MEMBERS_HEADING, "visible", "timeout=5s",
        )

    @keyword("I add ${username} to the project as ${role} via the UI")
    def add_member_ui(self, username: str, role: str) -> None:
        user_id = self._resolve_user_id(username)
        BuiltIn().run_keyword(
            "Select Options By", USER_SELECT, "value", str(user_id),
        )
        BuiltIn().run_keyword(
            "Select Options By", ROLE_SELECT, "value", role,
        )
        BuiltIn().run_keyword("Click", ADD_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", _member_row(username), "visible", "timeout=5s",
        )

    @keyword("I change ${username} role to ${role} via the UI")
    def change_member_role_ui(self, username: str, role: str) -> None:
        BuiltIn().run_keyword(
            "Select Options By", _member_role_select(username), "value", role,
        )

    @keyword("I remove ${username} from the project via the UI")
    def remove_member_ui(self, username: str) -> None:
        BuiltIn().run_keyword("Click", _member_remove(username))
        BuiltIn().run_keyword(
            "Wait For Elements State", _member_row(username), "hidden", "timeout=5s",
        )

    @keyword("the project members should include ${username}")
    def members_should_include(self, username: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _member_row(username), "visible", "timeout=5s",
        )

    @keyword("the project members should not include ${username}")
    def members_should_not_include(self, username: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _member_row(username), "hidden", "timeout=5s",
        )

    @keyword("the role of ${username} should be ${role}")
    def role_of_should_be(self, username: str, role: str) -> None:
        BuiltIn().run_keyword(
            "Get Selected Options",
            _member_role_select(username), "value", "==", role,
        )
