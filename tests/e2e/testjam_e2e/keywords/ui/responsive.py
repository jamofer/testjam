from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


HAMBURGER_BUTTON = 'button[aria-label="Open menu"]'
SIDEBAR = 'aside.bg-white.border-r'
SIDEBAR_BACKDROP = 'div[aria-hidden="true"].fixed.inset-0'
SIDEBAR_CLOSE_BUTTON = 'button[aria-label="Close menu"]'

MOBILE_WIDTH = 375
MOBILE_HEIGHT = 667
DESKTOP_WIDTH = 1280
DESKTOP_HEIGHT = 720


class ResponsiveUIMixin:
    """Browser keywords for mobile viewport + sidebar drawer."""

    @keyword("I switch to mobile viewport")
    def switch_to_mobile(self) -> None:
        BuiltIn().run_keyword(
            "Set Viewport Size", str(MOBILE_WIDTH), str(MOBILE_HEIGHT),
        )
        BuiltIn().run_keyword("Reload")

    @keyword("I switch to desktop viewport")
    def switch_to_desktop(self) -> None:
        BuiltIn().run_keyword(
            "Set Viewport Size", str(DESKTOP_WIDTH), str(DESKTOP_HEIGHT),
        )

    @keyword("the mobile menu button should be visible")
    def hamburger_visible(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", HAMBURGER_BUTTON, "visible", "timeout=5s",
        )

    @keyword("I open the mobile sidebar")
    def open_mobile_sidebar(self) -> None:
        BuiltIn().run_keyword("Click", HAMBURGER_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State",
            SIDEBAR_BACKDROP, "visible", "timeout=5s",
        )

    @keyword("I dismiss the mobile sidebar via the backdrop")
    def dismiss_via_backdrop(self) -> None:
        BuiltIn().run_keyword("Click", SIDEBAR_BACKDROP)
        BuiltIn().run_keyword(
            "Wait For Elements State",
            SIDEBAR_BACKDROP, "hidden", "timeout=5s",
        )

    @keyword("the mobile sidebar should be open")
    def sidebar_should_be_open(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            SIDEBAR_BACKDROP, "visible", "timeout=5s",
        )

    @keyword("the mobile sidebar should be closed")
    def sidebar_should_be_closed(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            SIDEBAR_BACKDROP, "hidden", "timeout=5s",
        )
