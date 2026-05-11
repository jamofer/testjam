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

    @keyword("the downloaded HTML report should embed ${filename} as a data url")
    def downloaded_report_should_embed_attachment(self, filename: str) -> None:
        body = self.last_download["body"]
        anchor = f'download="{filename}"'
        assert anchor in body, f"Attachment '{filename}' not embedded with download attribute"
        assert "data:" in body, "No data: URLs found in report"

    @keyword("the downloaded HTML report should mark ${filename} as unavailable")
    def downloaded_report_should_mark_unavailable(self, filename: str) -> None:
        body = self.last_download["body"]
        marker = f'class="hatt-missing"'
        assert marker in body, "No unavailable-attachment marker in report"
        assert filename in body, f"Attachment '{filename}' not referenced in report"
