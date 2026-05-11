import os
from pathlib import Path

from robot.api import logger
from robot.api.deco import keyword


class AttachmentsMixin:
    """Keywords covering execution + result attachments."""

    @keyword("I attach file ${path} to the execution")
    def attach_file_to_execution(self, path: str) -> int:
        return self._upload(f"/executions/{self.current_execution_id}/attachments", path)

    @keyword("I attach file ${path} to the current result")
    def attach_file_to_current_result(self, path: str) -> int:
        return self._upload(f"/results/{self.current_result_id}/attachments", path)

    @keyword("the execution should have ${count} attachments")
    def execution_should_have_attachments(self, count: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/attachments")
        assert response.status_code == 200, response.text
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} attachments, got {actual}"

    @keyword("the current result should have ${count} attachments")
    def result_should_have_attachments(self, count: str) -> None:
        response = self.client.get(f"/results/{self.current_result_id}/attachments")
        assert response.status_code == 200, response.text
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} attachments, got {actual}"

    @keyword("the execution attachments should contain ${filename}")
    def execution_attachments_should_contain(self, filename: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/attachments")
        names = [a["filename"] for a in response.json()]
        assert filename in names, f"'{filename}' not in {names}"

    @keyword("I delete the execution attachment named ${filename}")
    def delete_execution_attachment(self, filename: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/attachments")
        attachment = next((a for a in response.json() if a["filename"] == filename), None)
        assert attachment, f"Attachment '{filename}' not found"
        ack = self.client.delete(
            f"/executions/{self.current_execution_id}/attachments/{attachment['id']}",
        )
        assert ack.status_code == 204, ack.text

    def _upload(self, path: str, file_path: str) -> int:
        resolved = self._resolve_fixture(file_path)
        with open(resolved, "rb") as handle:
            response = self.client.post(
                path,
                files={"file": (resolved.name, handle, "application/octet-stream")},
            )
        assert response.status_code == 201, response.text
        attachment_id = response.json()["id"]
        logger.info(f"Uploaded '{resolved.name}' → attachment id={attachment_id}")
        return attachment_id

    def _resolve_fixture(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
            attempt = base / path
            if attempt.exists():
                return attempt
        raise AssertionError(f"Fixture not found: {path}")
