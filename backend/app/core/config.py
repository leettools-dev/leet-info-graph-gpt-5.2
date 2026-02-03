from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INFOGRAPH_",
        extra="ignore",
        # Load from .env in local development; do not commit secrets.
        env_file=".env",
    )

    # Security
    # IMPORTANT: set INFOGRAPH_SECRET_KEY in all non-dev environments.
    # For tests, a default is provided so importing modules doesn't require env wiring.
    secret_key: str = "dev-insecure-change-me"

    # Database
    database_url: str = "sqlite+aiosqlite:///./infograph.db"

    # Storage
    # If set, generated infographic images are written under this directory.
    # In production, replace with object storage (S3/GCS) and store only URLs.
    media_root: str = "./media"
    media_base_url: str = "http://localhost:8000/media"

    # OAuth (Google)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend
    frontend_origin: str = "http://localhost:5173"

    # Cookies
    cookie_secure: bool = False

    # Web search: rate limiting + caching
    # These are used to protect upstream services (e.g., DuckDuckGo HTML endpoint)
    # and to cache repeated queries.
    search_rate_per_minute: int = 20
    search_cache_ttl_seconds: int = 60 * 60
    search_cache_max_items: int = 512


    # Source fetch/ingest: rate limiting + caching
    fetch_rate_per_minute: int = 20
    fetch_cache_ttl_seconds: int = 60 * 60
    fetch_cache_max_items: int = 512


settings = Settings()
