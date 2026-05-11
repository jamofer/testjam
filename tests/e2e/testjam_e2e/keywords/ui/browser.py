import os

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


class BrowserMixin:
    """Browser lifecycle keywords."""

    @keyword("I open a headless browser")
    def open_headless_browser(self) -> None:
        BuiltIn().run_keyword("New Browser", "chromium", "headless=true")
        BuiltIn().run_keyword(
            "New Context",
            "viewport={'width': 1280, 'height': 800}",
            "ignoreHTTPSErrors=True",
        )
        self.frontend_url = os.getenv("TESTJAM_FRONTEND_URL", "http://localhost:5173").rstrip("/")

    @keyword("I close the browser")
    def close_browser(self) -> None:
        BuiltIn().run_keyword("Close Browser", "ALL")

    @keyword("the page title should contain ${text}")
    def page_title_should_contain(self, text: str) -> None:
        BuiltIn().run_keyword("Get Title", "contains", text)

    @keyword("the current url should contain ${fragment}")
    def current_url_should_contain(self, fragment: str) -> None:
        BuiltIn().run_keyword("Get Url", "contains", fragment)
