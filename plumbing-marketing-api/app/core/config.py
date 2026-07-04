"""Application settings (pydantic-settings) + SQLAlchemy URL helpers.

The app runtime uses the async driver (asyncpg). Alembic uses a sync driver
(psycopg) derived from the same DATABASE_URL, so there is a single source of
truth for the connection string.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # app
    APP_NAME: str = "Plumbing Marketing API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DEFAULT_TIMEZONE: str = "America/New_York"

    # database — canonical async DSN
    DATABASE_URL: str = (
        "postgresql+asyncpg://plumbing_app:change_me@postgres:5432/plumbing_marketing"
    )

    # auth / integrations
    INTERNAL_API_TOKEN: str = ""
    BREVO_API_KEY: str = ""
    BREVO_BASE_URL: str = "https://api.brevo.com/v3"
    GATEWAYAPI_API_TOKEN: str = ""
    GATEWAYAPI_BASE_URL: str = "https://gatewayapi.com/rest"
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    RESEND_API_KEY: str = ""

    @property
    def async_database_url(self) -> str:
        """DSN for the app's async engine (asyncpg)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):  # some providers emit this
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def alembic_database_url(self) -> str:
        """Sync DSN for Alembic (psycopg v3). Derived from the same DATABASE_URL."""
        url = self.DATABASE_URL
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "+psycopg")
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
