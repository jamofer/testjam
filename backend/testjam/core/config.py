from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Testjam API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://testjam:testjam@db:5432/testjam"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    class Config:
        env_file = ".env"


settings = Settings()
