"""Application settings, loaded from environment / .env (pydantic-settings)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # app
    APP_NAME: str = "Acme Plumbing Marketing Backend"
    APP_ENV: str = "dev"                      # dev | staging | production
    APP_DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DEFAULT_TIMEZONE: str = "America/New_York"

    # database (plain postgresql:// DSN; converted to asyncpg below)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/acme_marketing"

    # CORS — comma-separated origins; empty disables the middleware
    CORS_ORIGINS: str = ""

    # Brevo (marketing contacts + lifecycle email)
    BREVO_API_KEY: str = ""
    BREVO_BASE_URL: str = "https://api.brevo.com/v3"

    # GatewayAPI (SMS)
    GATEWAYAPI_API_TOKEN: str = ""
    GATEWAYAPI_BASE_URL: str = "https://gatewayapi.com/rest"

    # transactional email providers
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    RESEND_API_KEY: str = ""

    # internal auth for non-public callers (n8n, admin scripts)
    INTERNAL_API_TOKEN: str = "change_me_internal_token"

    # inbound webhook security
    MAILGUN_WEBHOOK_SIGNING_KEY: str = ""     # HMAC-SHA256 key for Mailgun webhooks
    BREVO_WEBHOOK_SECRET: str = ""            # shared secret sent by Brevo (header/token)

    # lifecycle automation
    DEFAULT_REVIEW_URL: str = "https://g.page/r/example/review"
    REVIEW_REQUEST_DEFAULT_DELAY_MINUTES: int = 120
    APPOINTMENT_REMINDER_LEAD_HOURS: int = 24

    # feature flags — let ops disable side-effecting paths without a redeploy
    ENABLE_WEBHOOK_PROCESSING: bool = True    # False = store raw only, no reconciliation
    ENABLE_AUTOMATION_ENDPOINTS: bool = True  # False = /automations/* returns 503

    @property
    def database_url_async(self) -> str:
        """DSN for the asyncpg driver, derived from the plain DSN."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
