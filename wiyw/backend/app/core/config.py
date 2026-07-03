"""Environment configuration for the WiYW backend. Fails fast on missing critical vars."""
import os


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    # app
    APP_ENV = os.environ.get("APP_ENV", "production")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    BRAND = "What's in Your Water"
    BRAND_PHONE = os.environ.get("BRAND_PHONE", "")
    OWNER_ALERT_PHONE = os.environ.get("OWNER_ALERT_PHONE", "")
    REVIEW_SHORTLINK_BASE = os.environ.get("REVIEW_SHORTLINK_BASE", "")
    PRIMARY_BOOKING_URL = os.environ.get("PRIMARY_BOOKING_URL", "")
    GBP_REVIEW_URL = os.environ.get("GBP_REVIEW_URL", "")

    # database (system of record)
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # transactional email: Resend primary, Mailgun failover + inbound
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "")
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")

    # marketing email: Brevo
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
    BREVO_WEBHOOK_TOKEN = os.environ.get("BREVO_WEBHOOK_TOKEN", "")
    BREVO_LIST_NEW_LEADS = int(os.environ.get("BREVO_LIST_NEW_LEADS", "2"))
    BREVO_LIST_CUSTOMERS = int(os.environ.get("BREVO_LIST_CUSTOMERS", "3"))
    BREVO_LIST_REACTIVATION = int(os.environ.get("BREVO_LIST_REACTIVATION", "4"))

    # SMS: GatewayAPI
    GATEWAYAPI_TOKEN = os.environ.get("GATEWAYAPI_TOKEN", "")
    GATEWAYAPI_SENDER = os.environ.get("GATEWAYAPI_SENDER", "WiYW")
    GATEWAYAPI_WEBHOOK_SECRET = os.environ.get("GATEWAYAPI_WEBHOOK_SECRET", "")

    # CMS: Storyblok
    STORYBLOK_WEBHOOK_SECRET = os.environ.get("STORYBLOK_WEBHOOK_SECRET", "")

    # third-party form vendors posting into /webhooks/forms
    FORMS_WEBHOOK_TOKEN = os.environ.get("FORMS_WEBHOOK_TOKEN", "")

    # internal auth (n8n / admin → /integrations/*, dashboard)
    INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")

    # CORS (public site origins)
    CORS_ORIGINS = _csv(os.environ.get("CORS_ORIGINS", ""))

    # Critical vars that must be present at boot.
    _REQUIRED = ("DATABASE_URL", "RESEND_API_KEY", "GATEWAYAPI_TOKEN", "OWNER_ALERT_PHONE")

    @classmethod
    def validate(cls) -> None:
        """Assert all critical env vars are set. Raises RuntimeError listing gaps."""
        missing = [k for k in cls._REQUIRED if not getattr(cls, k)]
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


config = Config()
