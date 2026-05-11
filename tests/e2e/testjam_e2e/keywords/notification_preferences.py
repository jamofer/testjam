from robot.api import logger
from robot.api.deco import keyword


class NotificationPreferencesMixin:
    """Keywords covering per-user notification preferences."""

    BASE = "/users/me/notification-preferences"

    @keyword("I fetch my notification preferences")
    def fetch_preferences(self) -> list:
        response = self.client.get(self.BASE)
        assert response.status_code == 200, response.text
        return response.json()

    @keyword("I disable email notifications for ${event_type}")
    def disable_email(self, event_type: str) -> None:
        self._patch(event_type, in_app=True, email=False)

    @keyword("I enable email notifications for ${event_type}")
    def enable_email(self, event_type: str) -> None:
        self._patch(event_type, in_app=True, email=True)

    @keyword("I disable in-app notifications for ${event_type}")
    def disable_in_app(self, event_type: str) -> None:
        self._patch(event_type, in_app=False, email=False)

    @keyword("I set ${event_type} preferences to in-app ${in_app} email ${email}")
    def set_preferences(self, event_type: str, in_app: str, email: str) -> None:
        self._patch(event_type, in_app=_truthy(in_app), email=_truthy(email))

    @keyword("the ${event_type} preference should be in-app ${in_app} email ${email}")
    def preference_should_be(self, event_type: str, in_app: str, email: str) -> None:
        response = self.client.get(f"{self.BASE}/{event_type}")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["in_app"] is _truthy(in_app), (
            f"Expected in_app={in_app}, got {body['in_app']}"
        )
        assert body["email"] is _truthy(email), (
            f"Expected email={email}, got {body['email']}"
        )

    @keyword("requesting preferences for ${event_type} should fail with ${status}")
    def request_unknown_event(self, event_type: str, status: str) -> None:
        response = self.client.get(f"{self.BASE}/{event_type}")
        assert response.status_code == int(status), (
            f"Expected HTTP {status}, got {response.status_code}: {response.text}"
        )

    @keyword("admin notification preferences are reset to defaults")
    def reset_admin_preferences(self) -> None:
        self.authenticate_as_admin()
        self._patch("execution_assigned", in_app=True, email=True)
        self._patch("execution_finished", in_app=True, email=False)
        self._patch("execution_failed", in_app=True, email=True)

    def _patch(self, event_type: str, *, in_app: bool, email: bool) -> None:
        response = self.client.put(
            f"{self.BASE}/{event_type}",
            json={"in_app": in_app, "email": email},
        )
        assert response.status_code == 200, response.text
        logger.info(f"Set {event_type} → in_app={in_app}, email={email}")


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "on")
