from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


PROFILE_HEADING = 'h1:has-text("Profile")'
CURRENT_PASSWORD_INPUT = 'form:has(h2:has-text("Change password")) input[type="password"] >> nth=0'
NEW_PASSWORD_INPUT = 'form:has(h2:has-text("Change password")) input[type="password"] >> nth=1'
CONFIRM_PASSWORD_INPUT = 'form:has(h2:has-text("Change password")) input[type="password"] >> nth=2'
CHANGE_PASSWORD_BUTTON = 'form:has(h2:has-text("Change password")) button:has-text("Change password")'

TOKEN_NAME_INPUT = 'form:has(input[placeholder="Token name"]) input[placeholder="Token name"]'
TOKEN_CREATE_BUTTON = 'form:has(input[placeholder="Token name"]) button:has-text("New token")'
NEW_TOKEN_BANNER = 'p:has-text("Token created — copy it now")'

SMTP_BANNER = '[data-testid="smtp-not-configured-banner"]'


def _email_checkbox(title: str) -> str:
    return f'input[type="checkbox"][aria-label="Email for {title}"]'


class ProfileUIMixin:
    """Browser keywords driving the Profile page."""

    @keyword("I open the profile page")
    def open_profile(self) -> None:
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/profile")
        BuiltIn().run_keyword(
            "Wait For Elements State", PROFILE_HEADING, "visible", "timeout=5s",
        )

    @keyword("I change my password from ${current} to ${new} via the UI")
    def change_password_ui(self, current: str, new: str) -> None:
        BuiltIn().run_keyword("Fill Text", CURRENT_PASSWORD_INPUT, current)
        BuiltIn().run_keyword("Fill Text", NEW_PASSWORD_INPUT, new)
        BuiltIn().run_keyword("Fill Text", CONFIRM_PASSWORD_INPUT, new)
        BuiltIn().run_keyword("Click", CHANGE_PASSWORD_BUTTON)
        BuiltIn().run_keyword(
            "Get Text", CURRENT_PASSWORD_INPUT, "==", "",
        )

    @keyword("I create a personal token named ${name} via the UI")
    def create_personal_token_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Fill Text", TOKEN_NAME_INPUT, name)
        BuiltIn().run_keyword("Click", TOKEN_CREATE_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", NEW_TOKEN_BANNER, "visible", "timeout=5s",
        )

    @keyword("the personal tokens table should list ${name}")
    def tokens_should_list(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'td:text-is("{name}") >> nth=0', "visible", "timeout=5s",
        )

    @keyword("I toggle the email preference for ${event_title}")
    def toggle_email_preference(self, event_title: str) -> None:
        BuiltIn().run_keyword("Click", _email_checkbox(event_title))

    @keyword("the email preference for ${event_title} should be ${state}")
    def email_preference_state(self, event_title: str, state: str) -> None:
        target = "True" if state == "enabled" else "False"
        BuiltIn().run_keyword(
            "Get Checkbox State", _email_checkbox(event_title), "==", target,
        )

    @keyword("the SMTP not-configured banner should be visible")
    def smtp_banner_should_be_visible(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", SMTP_BANNER, "visible", "timeout=5s",
        )

    @keyword("the SMTP not-configured banner should be hidden")
    def smtp_banner_should_be_hidden(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", SMTP_BANNER, "hidden", "timeout=5s",
        )
