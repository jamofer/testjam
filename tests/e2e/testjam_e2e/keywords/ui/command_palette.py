from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


PALETTE_INPUT = 'input[placeholder*="Search projects"]'
PALETTE_DIALOG = '[role="dialog"]:has(input[placeholder*="Search projects"])'
PALETTE_ITEM = f'{PALETTE_DIALOG} [role="option"]'
SIDEBAR_PALETTE_TRIGGER = 'button:has(span:text-is("Search…"))'


class CommandPaletteUIMixin:
    """Browser keywords for the Ctrl+K command palette."""

    @keyword("I open the command palette via keyboard")
    def open_palette_via_keyboard(self) -> None:
        BuiltIn().run_keyword("Keyboard Key", "press", "Control+k")
        BuiltIn().run_keyword(
            "Wait For Elements State", PALETTE_INPUT, "visible", "timeout=5s",
        )

    @keyword("I open the command palette via the sidebar")
    def open_palette_via_sidebar(self) -> None:
        BuiltIn().run_keyword("Click", SIDEBAR_PALETTE_TRIGGER)
        BuiltIn().run_keyword(
            "Wait For Elements State", PALETTE_INPUT, "visible", "timeout=5s",
        )

    @keyword("I dismiss the command palette")
    def dismiss_palette(self) -> None:
        BuiltIn().run_keyword("Keyboard Key", "press", "Escape")
        BuiltIn().run_keyword(
            "Wait For Elements State", PALETTE_INPUT, "hidden", "timeout=5s",
        )

    @keyword("I search the palette for ${query}")
    def search_palette(self, query: str) -> None:
        BuiltIn().run_keyword("Fill Text", PALETTE_INPUT, query)

    @keyword("the palette should list ${title}")
    def palette_should_list(self, title: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{PALETTE_ITEM}:has-text("{title}")', "visible", "timeout=5s",
        )

    @keyword("the palette should report no matches")
    def palette_no_matches(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{PALETTE_DIALOG} >> text=No matches', "visible", "timeout=5s",
        )

    @keyword("I activate the first palette result")
    def activate_first_result(self) -> None:
        BuiltIn().run_keyword("Keyboard Key", "press", "Enter")
        BuiltIn().run_keyword(
            "Wait For Elements State", PALETTE_INPUT, "hidden", "timeout=5s",
        )
