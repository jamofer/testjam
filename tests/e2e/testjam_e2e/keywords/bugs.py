from robot.api import logger
from robot.api.deco import keyword


class BugsMixin:
    """Keywords covering bug tracking flows."""

    @keyword("I create a bug titled ${title}")
    def create_bug(self, title: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/bugs",
            json={"title": title, "severity": "medium"},
        )
        assert response.status_code == 201, f"Create bug failed: {response.text}"
        body = response.json()
        self.current_bug_id = body["id"]
        self.current_bug_number = body["number"]
        logger.info(f"Created bug #{body['number']} → id={body['id']}")
        return body["id"]

    @keyword("I create a critical bug titled ${title}")
    def create_critical_bug(self, title: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/bugs",
            json={"title": title, "severity": "critical"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        self.current_bug_id = body["id"]
        self.current_bug_number = body["number"]
        return body["id"]

    @keyword("I change the bug status to ${status}")
    def change_bug_status(self, status: str) -> None:
        response = self.client.post(
            f"/bugs/{self.current_bug_id}/status",
            json={"status": status},
        )
        assert response.status_code == 200, response.text

    @keyword("I comment on the bug with ${body}")
    def comment_on_bug(self, body: str) -> None:
        response = self.client.post(
            f"/bugs/{self.current_bug_id}/comments",
            json={"body": body},
        )
        assert response.status_code == 201, response.text

    @keyword("the bug should have status ${status}")
    def bug_status_should_be(self, status: str) -> None:
        response = self.client.get(f"/bugs/{self.current_bug_id}")
        assert response.status_code == 200
        actual = response.json()["status"]
        assert actual == status, f"Expected status '{status}', got '{actual}'"

    @keyword("the bug should have ${count} comments")
    def bug_should_have_comments(self, count: str) -> None:
        response = self.client.get(f"/bugs/{self.current_bug_id}/comments")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} comments, got {actual}"

    @keyword("the bug history should contain ${count} entries")
    def bug_history_should_contain(self, count: str) -> None:
        response = self.client.get(f"/bugs/{self.current_bug_id}/activity")
        assert response.status_code == 200
        rows = [row for row in response.json() if row.get("field") == "status"]
        actual = len(rows)
        assert actual == int(count), f"Expected {count} history entries, got {actual}"

    @keyword("I download the bug report as ${format}")
    def download_bug_report(self, format: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/bugs/report",
            params={"format": format},
        )
        self.last_status_code = response.status_code
        self.last_download = {"content": response.content, "content_type": response.headers.get("content-type")}

    @keyword("the downloaded bug report should be HTML")
    def downloaded_bug_report_should_be_html(self) -> None:
        assert self.last_download is not None
        assert self.last_download["content_type"].startswith("text/html"), self.last_download

    @keyword("the project should have ${count} bugs")
    def project_should_have_bugs(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}/bugs")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} bugs, got {actual}"

    @keyword("I attach file ${path} to the bug")
    def attach_file_to_bug(self, path: str) -> int:
        resolved = self._resolve_fixture(path)
        with open(resolved, "rb") as handle:
            response = self.client.post(
                f"/bugs/{self.current_bug_id}/attachments",
                files={"file": (resolved.name, handle, "application/octet-stream")},
            )
        assert response.status_code == 201, response.text
        attachment_id = response.json()["id"]
        logger.info(f"Uploaded '{resolved.name}' to bug → attachment id={attachment_id}")
        return attachment_id

    @keyword("the bug should have ${count} attachments")
    def bug_should_have_attachments(self, count: str) -> None:
        response = self.client.get(f"/bugs/{self.current_bug_id}/attachments")
        assert response.status_code == 200, response.text
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} attachments, got {actual}"

    @keyword("the bug attachments should contain ${filename}")
    def bug_attachments_should_contain(self, filename: str) -> None:
        response = self.client.get(f"/bugs/{self.current_bug_id}/attachments")
        names = [row["filename"] for row in response.json()]
        assert filename in names, f"'{filename}' not in {names}"

    @keyword("I delete the bug attachment named ${filename}")
    def delete_bug_attachment(self, filename: str) -> None:
        attachment = self._find_bug_attachment(filename)
        ack = self.client.delete(
            f"/bugs/{self.current_bug_id}/attachments/{attachment['id']}",
        )
        assert ack.status_code == 204, ack.text

    @keyword("I try to download the bug attachment named ${filename}")
    def try_download_bug_attachment(self, filename: str) -> None:
        attachment = self._find_bug_attachment(filename)
        url = f"/bugs/{self.current_bug_id}/attachments/{attachment['id']}/download"
        self.last_status_code = self.client.get(url).status_code

    def _find_bug_attachment(self, filename: str) -> dict:
        response = self.client.get(f"/bugs/{self.current_bug_id}/attachments")
        assert response.status_code == 200, response.text
        attachment = next((row for row in response.json() if row["filename"] == filename), None)
        assert attachment, f"Attachment '{filename}' not found"
        return attachment
