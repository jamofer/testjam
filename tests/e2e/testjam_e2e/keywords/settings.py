from robot.api import logger
from robot.api.deco import keyword


class SettingsMixin:
    """Keywords covering admin AppSettings (private + public)."""

    @keyword("I sign out")
    def sign_out(self) -> None:
        self.client.clear_auth()

    @keyword("I reset settings to defaults")
    def reset_settings(self) -> None:
        self._patch_settings({
            "smtp_host": None,
            "smtp_port": None,
            "smtp_user": None,
            "smtp_from": None,
            "smtp_reply_to": None,
            "smtp_password": "",
            "smtp_use_tls": True,
            "ws_log_flush_ms": 100,
            "export_inline_attachment_mb": 10,
            "app_name": "Testjam",
            "allow_registration": True,
        })

    @keyword("settings are reset to defaults")
    def settings_are_reset(self) -> None:
        self.authenticate_as_admin()
        self.reset_settings()

    @keyword("I fetch the public settings")
    def fetch_public_settings(self) -> dict:
        response = self.client.get("/settings/public")
        assert response.status_code == 200, response.text
        return response.json()

    @keyword("I fetch the admin settings")
    def fetch_admin_settings(self) -> dict:
        response = self.client.get("/settings")
        assert response.status_code == 200, response.text
        return response.json()

    @keyword("I try to fetch the admin settings")
    def try_fetch_admin_settings(self) -> None:
        response = self.client.get("/settings")
        self.last_status_code = response.status_code

    @keyword("I configure SMTP host ${host} port ${port} from ${sender}")
    def configure_smtp(self, host: str, port: str, sender: str) -> None:
        self._patch_settings({
            "smtp_host": host,
            "smtp_port": int(port),
            "smtp_from": sender,
        })

    @keyword("I set the SMTP password to ${password}")
    def set_smtp_password(self, password: str) -> None:
        self._patch_settings({"smtp_password": password})

    @keyword("I clear the SMTP password")
    def clear_smtp_password(self) -> None:
        self._patch_settings({"smtp_password": ""})

    @keyword("I set the reply-to address to ${address}")
    def set_reply_to(self, address: str) -> None:
        self._patch_settings({"smtp_reply_to": address})

    @keyword("I set the log flush interval to ${ms} milliseconds")
    def set_log_flush_ms(self, ms: str) -> None:
        self._patch_settings({"ws_log_flush_ms": int(ms)})

    @keyword("I set the export inline attachment limit to ${mb} megabytes")
    def set_export_inline_attachment_mb(self, mb: str) -> None:
        self._patch_settings({"export_inline_attachment_mb": int(mb)})

    @keyword("I temporarily set the export inline attachment limit to ${mb} megabytes")
    def temp_set_export_inline_mb(self, mb: str) -> None:
        original = self.fetch_admin_settings()["export_inline_attachment_mb"]
        self._stash_setting("export_inline_attachment_mb", original)
        self._patch_settings({"export_inline_attachment_mb": int(mb)})

    @keyword("the previous settings values are restored")
    def restore_stashed_settings(self) -> None:
        if not getattr(self, "_settings_stash", None):
            return
        self.authenticate_as_admin()
        self._patch_settings(self._settings_stash)
        self._settings_stash = {}

    def _stash_setting(self, key: str, value) -> None:
        if not hasattr(self, "_settings_stash") or self._settings_stash is None:
            self._settings_stash = {}
        self._settings_stash.setdefault(key, value)

    @keyword("I set the app name to ${name}")
    def set_app_name(self, name: str) -> None:
        self._patch_settings({"app_name": name})

    @keyword("I disable self-registration")
    def disable_registration(self) -> None:
        self._patch_settings({"allow_registration": False})

    @keyword("the public settings app name should be ${name}")
    def public_app_name_should_be(self, name: str) -> None:
        body = self.fetch_public_settings()
        assert body["app_name"] == name, f"Expected '{name}', got '{body['app_name']}'"

    @keyword("the public settings should report SMTP as ${state}")
    def public_smtp_state_should_be(self, state: str) -> None:
        expected = _to_state(state)
        body = self.fetch_public_settings()
        assert body["smtp_configured"] is expected, (
            f"Expected smtp_configured={expected}, got {body['smtp_configured']}"
        )

    @keyword("the public settings should allow registration")
    def public_should_allow_registration(self) -> None:
        body = self.fetch_public_settings()
        assert body["allow_registration"] is True, "Self-registration is disabled"

    @keyword("the public settings should not allow registration")
    def public_should_not_allow_registration(self) -> None:
        body = self.fetch_public_settings()
        assert body["allow_registration"] is False, "Self-registration is enabled"

    @keyword("the SMTP password should be ${state}")
    def smtp_password_state_should_be(self, state: str) -> None:
        expected = _to_state(state)
        body = self.fetch_admin_settings()
        assert body["smtp_password_set"] is expected, (
            f"Expected smtp_password_set={expected}, got {body['smtp_password_set']}"
        )

    @keyword("the admin settings SMTP host should be ${host}")
    def smtp_host_should_be(self, host: str) -> None:
        body = self.fetch_admin_settings()
        assert body["smtp_host"] == host, f"Expected '{host}', got '{body['smtp_host']}'"

    @keyword("the admin settings reply-to should be ${address}")
    def smtp_reply_to_should_be(self, address: str) -> None:
        body = self.fetch_admin_settings()
        assert body["smtp_reply_to"] == address, (
            f"Expected '{address}', got '{body['smtp_reply_to']}'"
        )

    @keyword("the admin settings log flush interval should be ${ms} milliseconds")
    def ws_log_flush_ms_should_be(self, ms: str) -> None:
        body = self.fetch_admin_settings()
        assert body["ws_log_flush_ms"] == int(ms), (
            f"Expected ws_log_flush_ms={ms}, got {body['ws_log_flush_ms']}"
        )

    def _patch_settings(self, payload: dict) -> None:
        response = self.client.put("/settings", json=payload)
        assert response.status_code == 200, response.text
        logger.info(f"Updated settings: {sorted(payload)}")


def _to_state(value: str) -> bool:
    normalised = str(value).strip().lower()
    if normalised in ("configured", "true", "1", "set", "yes"):
        return True
    if normalised in ("not configured", "false", "0", "unset", "no", "not set"):
        return False
    raise ValueError(f"Unknown state '{value}'")
