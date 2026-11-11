"""The outbox runs listener jobs in order on its own thread."""
import threading

import pytest

from testjam_client.listener.outbox import WORKER_NAME, Outbox

GATE_TIMEOUT_SECONDS = 5


@pytest.fixture
def outbox():
    outbox = Outbox()
    yield outbox
    outbox.close()


def test_jobs_run_in_submission_order(outbox):
    calls = []

    for number in range(5):
        outbox.submit(calls.append, number)
    outbox.flush()

    assert calls == [0, 1, 2, 3, 4]


def test_jobs_run_on_the_worker_thread(outbox):
    threads = []

    outbox.submit(lambda: threads.append(threading.current_thread().name))
    outbox.flush()

    assert threads == [WORKER_NAME]


def test_submit_does_not_wait_for_a_busy_worker(outbox):
    gate = threading.Event()
    outbox.submit(gate.wait, GATE_TIMEOUT_SECONDS)

    outbox.submit(lambda: None)
    is_still_blocked = not gate.is_set()
    gate.set()

    assert is_still_blocked


def test_failing_job_does_not_stop_the_next_ones(outbox):
    calls = []

    outbox.submit(_explode)
    outbox.submit(calls.append, "after")
    outbox.flush()

    assert calls == ["after"]


def test_close_runs_pending_jobs_first():
    outbox = Outbox()
    calls = []
    gate = threading.Event()
    outbox.submit(gate.wait, GATE_TIMEOUT_SECONDS)
    outbox.submit(calls.append, "queued")

    gate.set()
    outbox.close()

    assert calls == ["queued"]


def test_close_twice_is_harmless():
    outbox = Outbox()
    outbox.close()

    outbox.close()


def _explode() -> None:
    raise RuntimeError("boom")
