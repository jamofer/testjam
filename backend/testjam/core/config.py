from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"


class Settings(BaseSettings):
    APP_NAME: str = "Testjam API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://testjam:testjam@db:5432/testjam"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    BCRYPT_ROUNDS: int = 12

    UPLOAD_DIR: str = "/app/uploads"

    # Fernet key used to encrypt integration credentials at rest. Must be a
    # urlsafe base64-encoded 32-byte key (`Fernet.generate_key()`). When empty,
    # integration push/sync endpoints refuse with 503.
    INTEGRATION_ENCRYPTION_KEY: str = ""
    INTEGRATION_HTTP_TIMEOUT_SECONDS: float = 15.0

    CORS_ORIGINS: str = DEFAULT_CORS_ORIGINS

    REDIS_URL: str | None = None
    REALTIME_CHANNEL_PREFIX: str = "testjam:rt"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
