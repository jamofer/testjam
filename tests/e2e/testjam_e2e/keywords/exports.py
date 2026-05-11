from robot.api import logger
from robot.api.deco import keyword


class ExportsMixin:
    """Keywords covering the HTML report export."""

    @keyword("I download the HTML report for the execution")
    def download_html_report(self) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/export/html")
        assert response.status_code == 200, response.text
        self.last_download = {
            "content_type": response.headers.get("content-type", ""),
            "body": response.text,
            "size": len(response.content),
        }
        logger.info(f"Downloaded HTML report ({self.last_download['size']} bytes)")

    @keyword("the downloaded HTML report should contain ${text}")
    def downloaded_report_should_contain(self, text: str) -> None:
        body = self.last_download["body"]
        assert text in body, f"'{text}' not in downloaded HTML report"

    @keyword("the downloaded HTML report content type should be html")
    def downloaded_content_type_should_be_html(self) -> None:
        actual = self.last_download["content_type"]
        assert "html" in actual.lower(), f"Expected html content type, got '{actual}'"

    @keyword("the downloaded HTML report should not be empty")
    def downloaded_report_should_not_be_empty(self) -> None:
        assert self.last_download["size"] > 0, "Downloaded report is empty"
