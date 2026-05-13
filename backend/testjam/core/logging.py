import json
import logging
import os
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_LOG_KEY = "request_id"
USER_ID_LOG_KEY = "user_id"

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_user_id: ContextVar[int | None] = ContextVar("user_id", default=None)


def configure_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        target = logging.getLogger(name)
        target.handlers = [handler]
        target.propagate = False
        target.setLevel(level)


def current_request_id() -> str | None:
    return _request_id.get()


def set_current_user_id(user_id: int | None) -> None:
    _user_id.set(user_id)


class JsonFormatter(logging.Formatter):
    DEFAULT_FIELDS = {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "message", "module",
        "msecs", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        request_id = _request_id.get()
        if request_id:
            payload[REQUEST_ID_LOG_KEY] = request_id
        user_id = _user_id.get()
        if user_id is not None:
            payload[USER_ID_LOG_KEY] = user_id
        for key, value in record.__dict__.items():
            if key not in self.DEFAULT_FIELDS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Generate request_id, expose it on the response, and emit one access log."""

    access_logger = logging.getLogger("testjam.access")

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request_token = _request_id.set(request_id)
        user_token = _user_id.set(None)

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self.access_logger.exception(
                "request failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "latency_ms": latency_ms,
                },
            )
            raise
        else:
            latency_ms = int((time.perf_counter() - started) * 1000)
            response.headers[REQUEST_ID_HEADER] = request_id
            self.access_logger.info(
                "request completed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                },
            )
            return response
        finally:
            _request_id.reset(request_token)
            _user_id.reset(user_token)
