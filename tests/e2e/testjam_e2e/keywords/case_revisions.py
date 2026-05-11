from robot.api.deco import keyword


class CaseRevisionsMixin:
    """Keywords covering the audit trail of a test case."""

    @keyword("the test case should have ${count} revisions")
    def case_should_have_revisions(self, count: str) -> None:
        response = self.client.get(f"/cases/{self.current_case_id}/revisions")
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} revisions, got {actual}"

    @keyword("the latest revision change kind should be ${kind}")
    def latest_revision_kind_should_be(self, kind: str) -> None:
        revisions = self.client.get(f"/cases/{self.current_case_id}/revisions").json()
        assert revisions, "No revisions found"
        actual = revisions[0]["change_kind"]
        assert actual == kind, f"Expected change_kind '{kind}', got '{actual}'"
