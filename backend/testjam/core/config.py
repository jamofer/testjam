import ipaddress
import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"

PLACEHOLDER_SECRET_KEYS = {"change-me-in-production", "change-me-use-openssl-rand-hex-32"}

HOST_LABEL = r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"
HOST_PATTERN = re.compile(rf"(\*\.)?{HOST_LABEL}(\.{HOST_LABEL})*")


class Settings(BaseSettings):
    APP_NAME: str = "Testjam API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://testjam:testjam@db:5432/testjam"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    BCRYPT_ROUNDS: int = 12

    UPLOAD_DIR: str = "/app/uploads"

    # Fernet key used to encrypt integration credentials at rest. Must be a
    # urlsafe base64-encoded 32-byte key (`Fernet.generate_key()`). When empty,
    # integration push/sync endpoints refuse with 503.
    INTEGRATION_ENCRYPTION_KEY: str = ""
    INTEGRATION_HTTP_TIMEOUT_SECONDS: float = 15.0

    # CSV of internal targets webhooks and integrations may reach besides public
    # addresses: IPs, CIDR ranges, hostnames or `*.domain` wildcards, e.g.
    # `gitlab.corp.example,*.ci.corp.example,10.20.0.0/16`. Everything else that
    # is not globally routable is refused.
    OUTBOUND_ALLOWED_HOSTS: str = ""

    CORS_ORIGINS: str = DEFAULT_CORS_ORIGINS

    REDIS_URL: str | None = None
    REALTIME_CHANNEL_PREFIX: str = "testjam:rt"

    # Hard cap on rows serialized into a single export (execution results,
    # exported test cases). Requests above the cap return 413 with a hint
    # to narrow the scope. Tune via the MAX_EXPORT_RESULTS env var.
    MAX_EXPORT_RESULTS: int = 5000

    # Chunk size for streaming exports back to the client. 64 KiB matches
    # the default uvicorn write buffer, so the kernel send queue stays warm
    # without holding the whole payload in a single Python bytes object.
    EXPORT_STREAM_CHUNK_BYTES: int = 64 * 1024

    # Per-file cap on attachments uploaded to bugs / cases / executions /
    # results / versions. The upload helper rejects anything larger with a
    # 413 before it ever hits disk. Default of 25 MiB is generous enough
    # for screenshots, junit bundles, and short screen recordings without
    # opening an obvious DOS by disk fill.
    MAX_ATTACHMENT_BYTES: int = 25 * 1024 * 1024

    # MIME types refused on attachment upload (415). Defaults block the
    # vectors that turn a download endpoint into a stored-XSS or RCE
    # primitive: anything the victim's browser will execute by itself
    # (HTML / JS / SVG with script support) and the obvious native
    # executable types. The list is a CSV so it can be overridden per
    # deployment via the BLOCKED_ATTACHMENT_MIME_TYPES env var.
    BLOCKED_ATTACHMENT_MIME_TYPES: str = (
        "text/html,application/xhtml+xml,application/javascript,"
        "text/javascript,image/svg+xml,application/x-msdownload,"
        "application/x-httpd-php,text/x-php"
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_insecure_secret_key(cls, value: str) -> str:
        if not value.strip() or value in PLACEHOLDER_SECRET_KEYS:
            raise ValueError("SECRET_KEY must be set to a random value, e.g. `openssl rand -hex 32`")
        return value

    @field_validator("OUTBOUND_ALLOWED_HOSTS")
    @classmethod
    def reject_invalid_outbound_hosts(cls, value: str) -> str:
        for entry in _split_entries(value):
            if _parse_network(entry) is None and not _is_host_pattern(entry):
                raise ValueError(f"OUTBOUND_ALLOWED_HOSTS entry is not an IP, CIDR or hostname: {entry}")
        return value

    @property
    def outbound_allowed_networks(self) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        networks = [_parse_network(entry) for entry in _split_entries(self.OUTBOUND_ALLOWED_HOSTS)]
        return [network for network in networks if network is not None]

    @property
    def outbound_allowed_host_patterns(self) -> list[str]:
        return [entry for entry in _split_entries(self.OUTBOUND_ALLOWED_HOSTS) if _parse_network(entry) is None]

    @property
    def blocked_attachment_mime_types(self) -> set[str]:
        return {item.strip().lower() for item in self.BLOCKED_ATTACHMENT_MIME_TYPES.split(",") if item.strip()}

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env")


def _split_entries(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _parse_network(entry: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        return ipaddress.ip_network(entry)
    except ValueError:
        return None


def _is_host_pattern(entry: str) -> bool:
    last_label = entry.rsplit(".", 1)[-1]
    return HOST_PATTERN.fullmatch(entry) is not None and not last_label.isdigit()


settings = Settings()
