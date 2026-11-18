"""Timestamps on the log lines the listener reports."""
import re
from datetime import datetime, timedelta, timezone

from testjam_client.listener.events import LogEvent
from testjam_client.listener.log import format_log_line, to_utc

PLUS_TWO = timezone(timedelta(hours=2))


def test_aware_timestamps_are_converted_to_utc():
    assert to_utc(datetime(2026, 11, 18, 11, 0, tzinfo=PLUS_TWO)) == datetime(
        2026, 11, 18, 9, 0, tzinfo=timezone.utc,
    )


def test_naive_robot_timestamps_are_read_as_runner_local_time():
    naive = datetime(2026, 11, 18, 11, 0)

    assert to_utc(naive) == naive.astimezone(timezone.utc)


def test_legacy_robot_timestamp_strings_are_parsed():
    assert to_utc("20240101 12:00:00.100") == datetime(2024, 1, 1, 12, 0, 0, 100000).astimezone(timezone.utc)


def test_a_message_without_timestamp_is_stamped_when_copied():
    event = LogEvent.from_robot(type("Message", (), {"level": "INFO", "message": "hi"})())

    assert datetime.now(timezone.utc) - event.timestamp < timedelta(seconds=5)


def test_log_line_carries_a_millisecond_utc_timestamp():
    stamp = datetime(2026, 11, 18, 11, 15, 2, 123456, tzinfo=PLUS_TWO)

    assert format_log_line("WARN", "slow", stamp) == "2026-11-18T09:15:02.123Z [WARN] slow"
