import time

import requests
from robot.api import logger
from robot.api.deco import keyword


DEFAULT_WAIT_SECONDS = 5


class MailpitMixin:
    """Keywords driving the Mailpit SMTP capture server.

    Every assertion scopes to a specific recipient address — mailpit is a
    single shared inbox across the orchestrator, so unfiltered "latest email"
    or "mailbox empty" queries race with concurrent suites. Always pass the
    test's expected recipient (e.g. ``bob@test.com``).
    """

    @keyword("I purge emails to ${recipient}")
    def purge_emails_to(self, recipient: str) -> None:
        ids = [m["ID"] for m in self._search(f'to:"{recipient}"')]
        if not ids:
            return
        response = requests.delete(
            f"{self.mailpit_url}/api/v1/messages",
            json={"ids": ids}, timeout=5,
        )
        response.raise_for_status()

    @keyword("I wait for ${count} emails to ${recipient}")
    def wait_for_emails_to(self, count: str, recipient: str) -> None:
        self._wait_for_count_to(int(count), recipient, DEFAULT_WAIT_SECONDS)

    @keyword("I wait for ${count} emails to ${recipient} within ${seconds} seconds")
    def wait_for_emails_to_within(self, count: str, recipient: str, seconds: str) -> None:
        self._wait_for_count_to(int(count), recipient, float(seconds))

    @keyword("the mailbox should have no emails to ${recipient}")
    def mailbox_should_have_none_to(self, recipient: str) -> None:
        matches = self._search(f'to:"{recipient}"')
        assert not matches, (
            f"Expected no emails to '{recipient}', got {len(matches)}"
        )

    @keyword("the mailbox should have ${count} emails to ${recipient}")
    def mailbox_should_have_count_to(self, count: str, recipient: str) -> None:
        matches = self._search(f'to:"{recipient}"')
        assert len(matches) == int(count), (
            f"Expected {count} emails to '{recipient}', got {len(matches)}"
        )

    @keyword("the latest email to ${recipient} subject should contain ${text}")
    def latest_subject_to_should_contain(self, recipient: str, text: str) -> None:
        latest = self._latest_to(recipient)
        assert text in latest["Subject"], (
            f"'{text}' not in subject '{latest['Subject']}'"
        )

    @keyword("the latest email to ${recipient} body should contain ${text}")
    def latest_body_to_should_contain(self, recipient: str, text: str) -> None:
        latest = self._latest_to(recipient)
        full = self._fetch_message(latest["ID"])
        body = (full.get("Text") or "") + (full.get("HTML") or "")
        assert text in body, f"'{text}' not in body of latest email to {recipient}"

    def _search(self, query: str) -> list[dict]:
        response = requests.get(
            f"{self.mailpit_url}/api/v1/search",
            params={"query": query}, timeout=5,
        )
        response.raise_for_status()
        return response.json().get("messages", [])

    def _fetch_message(self, message_id: str) -> dict:
        response = requests.get(
            f"{self.mailpit_url}/api/v1/message/{message_id}", timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def _latest_to(self, recipient: str) -> dict:
        matches = self._search(f'to:"{recipient}"')
        assert matches, f"No emails addressed to {recipient}"
        return matches[0]

    def _wait_for_count_to(self, target: int, recipient: str, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        latest_total = 0
        while time.monotonic() < deadline:
            matches = self._search(f'to:"{recipient}"')
            latest_total = len(matches)
            if latest_total >= target:
                return
            time.sleep(0.2)
        raise AssertionError(
            f"Only {latest_total}/{target} emails to {recipient} arrived within {seconds}s",
        )
