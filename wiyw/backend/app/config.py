"""Environment configuration for WiYW backend. Fails fast on missing critical vars."""
import os


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")
    GATEWAYAPI_TOKEN = os.environ.get("GATEWAYAPI_TOKEN", "")
    GATEWAYAPI_SENDER = os.environ.get("GATEWAYAPI_SENDER", "WiYW")
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
    STORYBLOK_WEBHOOK_SECRET = os.environ.get("STORYBLOK_WEBHOOK_SECRET", "")
    OWNER_ALERT_PHONE = os.environ.get("OWNER_ALERT_PHONE", "")
    REVIEW_SHORTLINK_BASE = os.environ.get("REVIEW_SHORTLINK_BASE", "")
    BRAND = "What's in Your Water"
    BRAND_PHONE = os.environ.get("BRAND_PHONE", "")

    # Critical vars that must be present at boot.
    _REQUIRED = ("DATABASE_URL", "RESEND_API_KEY", "GATEWAYAPI_TOKEN", "OWNER_ALERT_PHONE")

    @classmethod
    def validate(cls) -> None:
        """Assert all critical env vars are set. Raises RuntimeError listing gaps."""
        missing = [k for k in cls._REQUIRED if not getattr(cls, k)]
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


config = Config()
