from robot.api import logger
from robot.api.deco import keyword


class NotificationsMixin:
    """Keywords covering the in-app notification inbox."""

    @keyword("I have ${count} unread notifications")
    def should_have_unread_count(self, count: str) -> None:
        response = self.client.get("/notifications/unread-count")
        assert response.status_code == 200
        actual = response.json()["unread"]
        assert actual == int(count), f"Expected {count} unread, got {actual}"

    @keyword("the notifications inbox should be empty")
    def inbox_should_be_empty(self) -> None:
        response = self.client.get("/notifications")
        assert response.status_code == 200
        assert response.json() == [], f"Inbox not empty: {response.json()}"

    @keyword("the notifications inbox should have ${count} entries")
    def inbox_should_have(self, count: str) -> None:
        response = self.client.get("/notifications")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} notifications, got {actual}"

    @keyword("the latest notification should be of type ${event_type}")
    def latest_notification_should_be(self, event_type: str) -> None:
        response = self.client.get("/notifications", params={"limit": 1})
        assert response.status_code == 200
        body = response.json()
        assert body, "Inbox is empty"
        actual = body[0]["type"]
        assert actual == event_type, f"Expected type '{event_type}', got '{actual}'"

    @keyword("the latest notification message should contain ${text}")
    def latest_notification_message_should_contain(self, text: str) -> None:
        response = self.client.get("/notifications", params={"limit": 1})
        body = response.json()
        assert body, "Inbox is empty"
        assert text in body[0]["message"], (
            f"'{text}' not in '{body[0]['message']}'"
        )

    @keyword("I mark the latest notification as read")
    def mark_latest_as_read(self) -> None:
        response = self.client.get("/notifications", params={"limit": 1})
        body = response.json()
        assert body, "Inbox is empty"
        notification_id = body[0]["id"]
        ack = self.client.post(f"/notifications/{notification_id}/read")
        assert ack.status_code == 200, ack.text
        logger.info(f"Marked notification {notification_id} as read")

    @keyword("I mark all notifications as read")
    def mark_all_as_read(self) -> None:
        response = self.client.post("/notifications/read-all")
        assert response.status_code == 200, response.text

    @keyword("admin notifications are drained")
    def drain_admin_notifications(self) -> None:
        self.authenticate_as_admin()
        self.mark_all_as_read()

    @keyword("the inbox of ${username} is drained with password ${password}")
    def drain_user_inbox(self, username: str, password: str) -> None:
        self.log_in(username, password)
        self.mark_all_as_read()
        self.authenticate_as_admin()
