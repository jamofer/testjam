from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


BELL_BUTTON = 'button[aria-haspopup="dialog"][aria-label^="Notifications"]'
UNREAD_BADGE = '[data-testid="unread-badge"]'
DRAWER = '[role="dialog"][aria-label="Notifications"]'
DRAWER_ITEM = f'{DRAWER} ul > li'
DRAWER_UNREAD = f'{DRAWER} ul > li[class*="rose-50"]'
MARK_ALL_BUTTON = f'{DRAWER} button:has-text("Mark all read")'


class NotificationsUIMixin:
    """Browser keywords driving the notifications bell + drawer."""

    @keyword("I have a recipient ${username} with password ${password} expecting an assignment")
    def have_recipient_with_assignment(self, username: str, password: str) -> None:
        self.authenticate_as_admin()
        self.create_user(username, password)
        self.drain_user_inbox(username, password)
        self.have_fresh_project("UI-Notif-Project")
        self.start_execution_titled_assigned("UI Notif", username)
        self.switch_ui_session(username, password)

    @keyword("I have a recipient ${username} with password ${password} and no notifications")
    def have_recipient_clean(self, username: str, password: str) -> None:
        self.authenticate_as_admin()
        self.create_user(username, password)
        self.drain_user_inbox(username, password)
        self.switch_ui_session(username, password)

    def start_execution_titled_assigned(self, title: str, username: str) -> None:
        self.start_execution_assigned_to(title, username)

    @keyword("the notification badge should show ${count} unread")
    def badge_should_show(self, count: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", UNREAD_BADGE, "visible", "timeout=5s",
        )
        BuiltIn().run_keyword("Get Text", UNREAD_BADGE, "==", count)

    @keyword("the notification badge should be hidden")
    def badge_should_be_hidden(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", UNREAD_BADGE, "hidden", "timeout=5s",
        )

    @keyword("I open the notifications drawer")
    def open_drawer(self) -> None:
        BuiltIn().run_keyword("Click", BELL_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", DRAWER, "visible", "timeout=5s",
        )

    @keyword("the notifications drawer should list ${count} entries")
    def drawer_should_list(self, count: str) -> None:
        BuiltIn().run_keyword(
            "Get Element Count", DRAWER_ITEM, "==", int(count),
        )

    @keyword("the notifications drawer should list ${count} unread entries")
    def drawer_should_list_unread(self, count: str) -> None:
        BuiltIn().run_keyword(
            "Get Element Count", DRAWER_UNREAD, "==", int(count),
        )

    @keyword("the notifications drawer should be empty")
    def drawer_should_be_empty(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{DRAWER} >> text=No notifications', "visible", "timeout=5s",
        )

    @keyword("I mark all notifications as read via the UI")
    def mark_all_read_ui(self) -> None:
        BuiltIn().run_keyword("Click", MARK_ALL_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", MARK_ALL_BUTTON, "hidden", "timeout=5s",
        )
