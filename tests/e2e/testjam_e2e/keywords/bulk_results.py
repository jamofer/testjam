from robot.api import logger
from robot.api.deco import keyword


class BulkResultsMixin:
    """Keywords covering bulk result endpoint."""

    @keyword("I bulk report all results in the current execution as ${status}")
    def bulk_report_all_as(self, status: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        items = [
            {"test_case_id": result["test_case_id"], "status": status}
            for result in response.json()
        ]
        bulk = self.client.post(
            f"/executions/{self.current_execution_id}/results/bulk",
            json={"results": items},
        )
        assert bulk.status_code == 200, bulk.text
        self.last_bulk_response = bulk.json()
        logger.info(f"Bulk reported {len(items)} results as '{status}'")

    @keyword("I bulk report ${count} fake-case results as ${status}")
    def bulk_report_fake(self, count: str, status: str) -> None:
        items = [
            {"test_case_id": 999_000 + offset, "status": status}
            for offset in range(int(count))
        ]
        bulk = self.client.post(
            f"/executions/{self.current_execution_id}/results/bulk",
            json={"results": items},
        )
        assert bulk.status_code == 200, bulk.text
        self.last_bulk_response = bulk.json()

    @keyword("the bulk response should have ${created} created and ${updated} updated")
    def bulk_counts_should_be(self, created: str, updated: str) -> None:
        body = self.last_bulk_response
        assert body is not None, "No bulk response captured"
        assert body["created"] == int(created), (
            f"Expected created={created}, got {body['created']}"
        )
        assert body["updated"] == int(updated), (
            f"Expected updated={updated}, got {body['updated']}"
        )

    @keyword("the bulk response should have ${count} errors")
    def bulk_errors_should_be(self, count: str) -> None:
        body = self.last_bulk_response
        assert body is not None, "No bulk response captured"
        actual = len(body.get("errors", []))
        assert actual == int(count), f"Expected {count} errors, got {actual}"
