from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INFOGRAPH_", extra="ignore")

    # Security
    secret_key: str = "dev-insecure-change-me"

    # Database
    database_url: str = "sqlite+aiosqlite:///./infograph.db"

    # OAuth (Google)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend
    frontend_origin: str = "http://localhost:5173"

    # Cookies
    cookie_secure: bool = False


settings = Settings()
