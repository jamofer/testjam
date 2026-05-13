from robot.api.deco import keyword


class HealthMixin:
    """Keywords covering the operational /health endpoint."""

    @keyword("I check the health endpoint")
    def check_health(self) -> None:
        response = self.client.get_root("/health")
        self.last_status_code = response.status_code
        self.last_health_payload = response.json()

    @keyword("the health payload should report db ${expected}")
    def health_db_should_be(self, expected: str) -> None:
        actual = self.last_health_payload.get("db")
        assert actual == expected, f"Expected db={expected!r}, got {actual!r}"

    @keyword("the health payload should report status ${expected}")
    def health_status_should_be(self, expected: str) -> None:
        actual = self.last_health_payload.get("status")
        assert actual == expected, f"Expected status={expected!r}, got {actual!r}"

    @keyword("the health payload should report a non-empty version")
    def health_version_should_be_non_empty(self) -> None:
        version = self.last_health_payload.get("version")
        assert version, f"Expected non-empty version, got {version!r}"
