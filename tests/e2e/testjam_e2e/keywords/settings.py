from robot.api import logger
from robot.api.deco import keyword


class SettingsMixin:
    """Keywords that change admin AppSettings for one test and put them back.

    AppSettings are global: only change values no other suite reads, always
    through the temporary keywords, and restore them in the test teardown.
    """

    @keyword("I temporarily set the export inline attachment limit to ${mb} megabytes")
    def temp_set_export_inline_mb(self, mb: str) -> None:
        original = self._admin_settings()["export_inline_attachment_mb"]
        self._stash_setting("export_inline_attachment_mb", original)
        self._patch_settings({"export_inline_attachment_mb": int(mb)})

    @keyword("the previous settings values are restored")
    def restore_stashed_settings(self) -> None:
        if not getattr(self, "_settings_stash", None):
            return
        self.authenticate_as_admin()
        self._patch_settings(self._settings_stash)
        self._settings_stash = {}

    def _admin_settings(self) -> dict:
        response = self.client.get("/settings")
        assert response.status_code == 200, response.text
        return response.json()

    def _stash_setting(self, key: str, value) -> None:
        if not hasattr(self, "_settings_stash") or self._settings_stash is None:
            self._settings_stash = {}
        self._settings_stash.setdefault(key, value)

    def _patch_settings(self, payload: dict) -> None:
        response = self.client.put("/settings", json=payload)
        assert response.status_code == 200, response.text
        logger.info(f"Updated settings: {sorted(payload)}")
