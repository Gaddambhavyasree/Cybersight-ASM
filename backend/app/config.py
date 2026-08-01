from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "CyberSight ASM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "cybersight_asm"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "CyberSight ASM <noreply@cybersight.io>"

    FRONTEND_URL: str = "http://localhost:5173"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # Optional threat-intelligence provider credentials. Empty values disable
    # the corresponding provider without failing application startup.
    NVD_API_KEY: str = ""
    SHODAN_API_KEY: str = ""
    VT_API_KEY: str = ""

    class Config:
        # Resolve relative to the backend package so launching uvicorn from
        # the repository root does not silently load the unrelated root .env.
        env_file = str(BACKEND_ENV_FILE)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
