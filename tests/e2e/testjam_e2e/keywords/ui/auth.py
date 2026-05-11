from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


USERNAME_INPUT = 'input[name="username"]'
PASSWORD_INPUT = 'input[name="password"]'
SUBMIT_BUTTON = 'button[type="submit"]'
LOGIN_ERROR_TEXT = "p.text-red-500"


class AuthUIMixin:
    """Browser-driven authentication keywords."""

    @keyword("I open the login page")
    def open_login_page(self) -> None:
        BuiltIn().run_keyword("New Page", f"{self.frontend_url}/login")
        BuiltIn().run_keyword(
            "Wait For Elements State", USERNAME_INPUT, "visible", "timeout=10s",
        )

    @keyword("I submit the login form with ${username} and ${password}")
    def submit_login_form(self, username: str, password: str) -> None:
        BuiltIn().run_keyword("Fill Text", USERNAME_INPUT, username)
        BuiltIn().run_keyword("Fill Text", PASSWORD_INPUT, password)
        BuiltIn().run_keyword("Click", SUBMIT_BUTTON)

    @keyword("I should land on the projects page")
    def should_land_on_projects(self) -> None:
        BuiltIn().run_keyword("Wait For Load State", "networkidle", "timeout=10s")
        BuiltIn().run_keyword("Get Url", "contains", "/projects")

    @keyword("the login form should show error ${text}")
    def login_form_should_show_error(self, text: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", LOGIN_ERROR_TEXT, "visible", "timeout=10s",
        )
        BuiltIn().run_keyword("Get Text", LOGIN_ERROR_TEXT, "contains", text)

    @keyword("I sign in to the UI as ${username} with password ${password}")
    def sign_in_to_ui(self, username: str, password: str) -> None:
        self.open_headless_browser()
        self.open_login_page()
        self.submit_login_form(username, password)
        self.should_land_on_projects()

    @keyword("I switch the UI session to ${username} with password ${password}")
    def switch_ui_session(self, username: str, password: str) -> None:
        BuiltIn().run_keyword("LocalStorage Clear")
        self.open_login_page()
        self.submit_login_form(username, password)
        self.should_land_on_projects()
