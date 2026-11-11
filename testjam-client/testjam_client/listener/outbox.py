"""Runs listener work on a background thread so Robot never waits on the API.

Robot calls listeners on the thread that runs the tests, so every HTTP round
trip made there stretches the run. The outbox queues each job and a single
worker runs them in submission order, which keeps the reporter's state machine
sequential without locks.
"""
from __future__ import annotations

import functools
import logging
import queue
import threading
from collections.abc import Callable
from typing import Any

log = logging.getLogger("testjam.listener")

WORKER_NAME = "testjam-listener"
_STOP = object()


class Outbox:
    def __init__(self) -> None:
        self._jobs: queue.Queue[Any] = queue.Queue()
        self._worker = threading.Thread(target=self._run, name=WORKER_NAME, daemon=True)
        self._worker.start()

    def submit(self, job: Callable[..., Any], *arguments: Any) -> None:
        self._jobs.put(functools.partial(job, *arguments))

    def flush(self) -> None:
        """Block until every job submitted so far has run."""
        self._jobs.join()

    def close(self) -> None:
        """Run the pending jobs, then stop the worker."""
        if not self._worker.is_alive():
            return
        self._jobs.put(_STOP)
        self._worker.join()

    def _run(self) -> None:
        while (job := self._jobs.get()) is not _STOP:
            self._execute(job)
        self._jobs.task_done()

    def _execute(self, job: Callable[[], Any]) -> None:
        try:
            job()
        except Exception:
            log.exception("Testjam listener job failed")
        finally:
            self._jobs.task_done()
