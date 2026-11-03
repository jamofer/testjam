from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

FORGOT_EMAIL_INPUT = 'input#email'
FORGOT_SUBMIT = 'button[type="submit"]'
RESET_NEW_PASSWORD = 'input#new-password'
RESET_CONFIRM_PASSWORD = 'input#confirm-password'
RESET_SUBMIT = 'button[type="submit"]'


class PasswordResetUIMixin:
    """Browser keywords for the forgot / reset password pages."""

    @keyword("I request a password reset for ${email} via the UI")
    def request_reset_via_ui(self, email: str) -> None:
        BuiltIn().run_keyword("New Page", f"{self.frontend_url}/forgot-password")
        BuiltIn().run_keyword("Fill Text", FORGOT_EMAIL_INPUT, email)
        BuiltIn().run_keyword("Click", FORGOT_SUBMIT)

    @keyword("I follow the reset link sent to ${email} and choose ${password}")
    def follow_reset_link(self, email: str, password: str) -> None:
        self.wait_for_emails_to("1", email)
        token = self.extract_reset_token_for(email)
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/reset-password?token={token}")
        BuiltIn().run_keyword("Fill Text", RESET_NEW_PASSWORD, password)
        BuiltIn().run_keyword("Fill Text", RESET_CONFIRM_PASSWORD, password)
        BuiltIn().run_keyword("Click", RESET_SUBMIT)
        BuiltIn().run_keyword("Wait For Elements State", 'input[name="username"]', "visible", "timeout=10s")
