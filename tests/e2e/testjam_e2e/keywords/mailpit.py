import time

import requests
from robot.api import logger
from robot.api.deco import keyword


DEFAULT_WAIT_SECONDS = 5


class MailpitMixin:
    """Keywords covering the Mailpit SMTP capture server."""

    @keyword("the mailbox is purged")
    def purge_mailbox(self) -> None:
        response = requests.delete(f"{self.mailpit_url}/api/v1/messages", timeout=5)
        response.raise_for_status()

    @keyword("the email pipeline is reset")
    def reset_email_pipeline(self) -> None:
        self.purge_mailbox()
        self.authenticate_as_admin()
        self.reset_settings()
        self.mark_all_as_read()
        self.reset_admin_preferences()

    @keyword("I configure SMTP to use mailpit")
    def configure_smtp_for_mailpit(self) -> None:
        host = self.mailpit_url.replace("https://", "").replace("http://", "").split(":")[0]
        self._patch_settings({
            "smtp_host": host,
            "smtp_port": 1025,
            "smtp_from": "noreply@testjam.test",
            "smtp_use_tls": False,
        })

    @keyword("the mailbox should contain ${count} emails")
    def mailbox_should_contain(self, count: str) -> None:
        body = self._list_messages()
        assert body["total"] == int(count), (
            f"Expected {count} emails, got {body['total']}"
        )

    @keyword("the mailbox should be empty")
    def mailbox_should_be_empty(self) -> None:
        body = self._list_messages()
        assert body["total"] == 0, f"Expected empty mailbox, got {body['total']} emails"

    @keyword("I wait for ${count} emails in the mailbox")
    def wait_for_emails(self, count: str) -> None:
        self._wait_for_count(int(count), DEFAULT_WAIT_SECONDS)

    @keyword("I wait for ${count} emails in the mailbox within ${seconds} seconds")
    def wait_for_emails_within(self, count: str, seconds: str) -> None:
        self._wait_for_count(int(count), float(seconds))

    @keyword("the mailbox should contain an email to ${address}")
    def mailbox_should_have_email_to(self, address: str) -> None:
        for message in self._list_messages()["messages"]:
            if address in _recipients(message):
                return
        raise AssertionError(f"No email addressed to '{address}'")

    @keyword("the mailbox should contain ${count} emails to ${address}")
    def mailbox_should_have_count_emails_to(self, count: str, address: str) -> None:
        matches = [
            m for m in self._list_messages()["messages"]
            if address in _recipients(m)
        ]
        assert len(matches) == int(count), (
            f"Expected {count} emails to '{address}', got {len(matches)}"
        )

    @keyword("the latest email subject should contain ${text}")
    def latest_subject_should_contain(self, text: str) -> None:
        latest = self._latest_message()
        assert text in latest["Subject"], (
            f"'{text}' not in subject '{latest['Subject']}'"
        )

    @keyword("the latest email recipient should be ${address}")
    def latest_recipient_should_be(self, address: str) -> None:
        latest = self._latest_message()
        addresses = _recipients(latest)
        assert address in addresses, f"'{address}' not in {addresses}"

    @keyword("the latest email body should contain ${text}")
    def latest_body_should_contain(self, text: str) -> None:
        latest = self._latest_message()
        full = self._fetch_message(latest["ID"])
        body = (full.get("Text") or "") + (full.get("HTML") or "")
        assert text in body, f"'{text}' not in body of latest email"

    def _list_messages(self) -> dict:
        response = requests.get(f"{self.mailpit_url}/api/v1/messages", timeout=5)
        response.raise_for_status()
        return response.json()

    def _fetch_message(self, message_id: str) -> dict:
        response = requests.get(
            f"{self.mailpit_url}/api/v1/message/{message_id}", timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def _latest_message(self) -> dict:
        body = self._list_messages()
        assert body["messages"], "Mailbox is empty"
        return body["messages"][0]

    def _wait_for_count(self, target: int, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        latest_total = 0
        while time.monotonic() < deadline:
            body = self._list_messages()
            latest_total = body["total"]
            if latest_total >= target:
                return
            time.sleep(0.2)
        raise AssertionError(
            f"Only {latest_total}/{target} emails arrived within {seconds}s",
        )


def _recipients(message: dict) -> list[str]:
    return [recipient["Address"] for recipient in message.get("To") or []]
