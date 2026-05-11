from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


SETTINGS_HEADING = 'h1:has-text("Settings")'
SAVE_BUTTON = 'button:has-text("Save")'
SMTP_HOST_INPUT = 'input[placeholder="smtp.example.com"]'
SMTP_PORT_INPUT = 'input[placeholder="587"]'
SMTP_FROM_INPUT = 'input[placeholder="noreply@example.com"]'
WS_LOG_FLUSH_INPUT = 'section:has(h2:has-text("Real-time")) input[type="number"]'


class SettingsUIMixin:
    """Browser keywords driving the admin Settings page."""

    @keyword("I open the settings page")
    def open_settings(self) -> None:
        BuiltIn().run_keyword("Go To", f"{self.frontend_url}/settings")
        BuiltIn().run_keyword(
            "Wait For Elements State", SETTINGS_HEADING, "visible", "timeout=5s",
        )

    @keyword("I fill the SMTP form with host ${host} port ${port} from ${sender}")
    def fill_smtp_form(self, host: str, port: str, sender: str) -> None:
        BuiltIn().run_keyword("Fill Text", SMTP_HOST_INPUT, host)
        BuiltIn().run_keyword("Fill Text", SMTP_PORT_INPUT, port)
        BuiltIn().run_keyword("Fill Text", SMTP_FROM_INPUT, sender)

    @keyword("I set the log flush interval to ${ms} via the UI")
    def set_log_flush_ui(self, ms: str) -> None:
        BuiltIn().run_keyword("Fill Text", WS_LOG_FLUSH_INPUT, ms)

    @keyword("I save the settings form")
    def save_settings(self) -> None:
        BuiltIn().run_keyword("Click", SAVE_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Response",
            "matcher=**/api/v1/settings", "timeout=5s",
        )

    @keyword("the log flush interval input should read ${ms}")
    def log_flush_input_should_read(self, ms: str) -> None:
        BuiltIn().run_keyword(
            "Get Attribute", WS_LOG_FLUSH_INPUT, "value", "==", ms,
        )
