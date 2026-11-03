from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

LANGUAGE_GROUP = '[role="radiogroup"]'


class LocaleUIMixin:
    """Browser keywords for switching the interface language."""

    @keyword("I switch the interface language to ${language} via the UI")
    def switch_language(self, language: str) -> None:
        BuiltIn().run_keyword("Click", f'{LANGUAGE_GROUP} button[role="radio"]:has-text("{language}")')

    @keyword("the sidebar should offer ${label}")
    def sidebar_should_offer(self, label: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", f'[data-testid="sidebar"] >> text="{label}"', "visible", "timeout=10s",
        )

    @keyword("my saved language should be ${locale}")
    def saved_language_should_be(self, locale: str) -> None:
        actual = self.client.get("/users/me").json()["locale"]
        assert actual == locale, f"Saved locale is '{actual}', expected '{locale}'"
