from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


class Settings(BaseSettings):
    REDIS_URL: str
    DATABASE_URL: str
    SECRET_KEY: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    AWS_KEY_ID: str
    AWS_SECRET_KEY: str
    BUCKET_NAME: str
    TURNSTILE_SECRET_KEY: str
    SENTRY_DNS: Optional[str] = None
    ALGORITHM: str = "HS256"
    POW_BITS: int = 16

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
