import json
import time

import websocket
from robot.api import logger
from robot.api.deco import keyword


DEFAULT_RECEIVE_TIMEOUT_SECONDS = 5
ACK_TIMEOUT_SECONDS = 2


class WebsocketMixin:
    """Keywords covering the multi-topic WebSocket endpoint."""

    @keyword("I open a websocket")
    def open_websocket(self) -> None:
        token = self._bearer_token()
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_base}/ws?token={token}"
        self.websocket = websocket.create_connection(url, timeout=DEFAULT_RECEIVE_TIMEOUT_SECONDS)
        self.last_websocket_frame = None
        logger.info(f"WebSocket open → {url}")

    @keyword("I open a websocket as ${username} with password ${password}")
    def open_websocket_as(self, username: str, password: str) -> None:
        self.log_in(username, password)
        self.open_websocket()

    @keyword("I try to open a websocket with token ${token}")
    def try_open_websocket(self, token: str) -> None:
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_base}/ws?token={token}"
        try:
            self.websocket = websocket.create_connection(url, timeout=DEFAULT_RECEIVE_TIMEOUT_SECONDS)
            self.last_status_code = 101
        except websocket.WebSocketBadStatusException as exc:
            self.last_status_code = exc.status_code

    @keyword("I subscribe to topic ${topic}")
    def subscribe(self, topic: str) -> None:
        self._send({"action": "subscribe", "topic": topic})
        self._receive_until(lambda frame: frame.get("topic") == topic)
        assert self.last_websocket_frame["event"] == "subscribed", (
            f"Expected 'subscribed' ack, got {self.last_websocket_frame}"
        )

    @keyword("I subscribe to my user topic")
    def subscribe_to_my_user_topic(self) -> None:
        me = self.client.get("/users/me").json()
        self.subscribe(f"user:{me['id']}")

    @keyword("I subscribe to the current project topic")
    def subscribe_to_current_project(self) -> None:
        self.subscribe(f"project:{self.current_project_id}")

    @keyword("I subscribe to the current execution topic")
    def subscribe_to_current_execution(self) -> None:
        self.subscribe(f"execution:{self.current_execution_id}")

    @keyword("I try to subscribe to topic ${topic}")
    def try_subscribe(self, topic: str) -> None:
        self._send({"action": "subscribe", "topic": topic})
        self._receive_until(lambda frame: frame.get("topic") == topic)

    @keyword("I try to subscribe to the user topic of ${username}")
    def try_subscribe_to_user_topic(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        self.try_subscribe(f"user:{user_id}")

    @keyword("I unsubscribe from topic ${topic}")
    def unsubscribe(self, topic: str) -> None:
        self._send({"action": "unsubscribe", "topic": topic})
        self._receive_until(
            lambda frame: frame.get("event") == "unsubscribed" and frame.get("topic") == topic,
        )

    @keyword("I send a pong frame")
    def send_pong(self) -> None:
        self._send({"action": "pong"})

    @keyword("I should receive a ${event} event within ${seconds} seconds")
    def expect_event(self, event: str, seconds: str) -> None:
        deadline = time.monotonic() + float(seconds)
        while time.monotonic() < deadline:
            remaining = max(0.05, deadline - time.monotonic())
            self.websocket.settimeout(remaining)
            try:
                raw = self.websocket.recv()
            except websocket.WebSocketTimeoutException:
                break
            frame = json.loads(raw)
            self.last_websocket_frame = frame
            if frame.get("event") == event:
                return
        raise AssertionError(
            f"Did not receive event '{event}' within {seconds}s; last frame={self.last_websocket_frame}",
        )

    @keyword("the last websocket frame event should be ${event}")
    def last_event_should_be(self, event: str) -> None:
        assert self.last_websocket_frame is not None, "No websocket frame captured yet"
        actual = self.last_websocket_frame.get("event")
        assert actual == event, f"Expected event '{event}', got '{actual}'"

    @keyword("the last websocket frame should be an error with reason ${reason}")
    def last_error_reason_should_be(self, reason: str) -> None:
        assert self.last_websocket_frame is not None, "No websocket frame captured yet"
        assert self.last_websocket_frame.get("event") == "error", (
            f"Expected error frame, got {self.last_websocket_frame}"
        )
        actual = self.last_websocket_frame.get("error")
        assert actual == reason, f"Expected error '{reason}', got '{actual}'"

    @keyword("the last websocket payload field ${field} should be ${value}")
    def last_payload_field_should_be(self, field: str, value: str) -> None:
        assert self.last_websocket_frame is not None, "No websocket frame captured yet"
        data = self.last_websocket_frame.get("data") or {}
        actual = data.get(field)
        assert str(actual) == value, f"Expected {field}={value}, got {actual}"

    @keyword("the last websocket payload entries should contain message ${text}")
    def last_payload_entries_should_contain(self, text: str) -> None:
        data = (self.last_websocket_frame or {}).get("data") or {}
        entries = data.get("entries") or []
        joined = "\n".join(entry.get("message", "") for entry in entries)
        assert text in joined, f"'{text}' not in log entries:\n{joined}"

    @keyword("I close the websocket")
    def close_websocket(self) -> None:
        if self.websocket is not None:
            try:
                self.websocket.close()
            except Exception:
                pass
            self.websocket = None

    def _bearer_token(self) -> str:
        auth = self.client.session.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        assert token, "No bearer token set — call 'I am authenticated as admin' first"
        return token

    def _send(self, payload: dict) -> None:
        assert self.websocket is not None, "WebSocket not open"
        self.websocket.send(json.dumps(payload))

    def _receive_until(self, predicate, timeout: float = ACK_TIMEOUT_SECONDS) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = max(0.05, deadline - time.monotonic())
            self.websocket.settimeout(remaining)
            try:
                raw = self.websocket.recv()
            except websocket.WebSocketTimeoutException:
                break
            frame = json.loads(raw)
            self.last_websocket_frame = frame
            if predicate(frame):
                return
        raise AssertionError(
            f"Predicate not satisfied within {timeout}s; last frame={self.last_websocket_frame}",
        )
