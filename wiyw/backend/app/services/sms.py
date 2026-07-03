"""SMS service: GatewayAPI transport + WiYW message templates."""
from typing import Optional

from ..core.config import config
from ..integrations import gatewayapi


async def send_sms(msisdn: str, message: str) -> tuple[bool, Optional[str]]:
    """Send one SMS. Returns (success, provider_msg_id). Never raises."""
    return await gatewayapi.send_sms(msisdn, message)


# ── templates (sms_* keys per naming conventions) ────────────────────

def lead_confirm_text(name: str) -> str:                       # sms_lead_confirm
    return (f"{config.BRAND}: Thanks {name}! We got your request and will call "
            f"you shortly. Need us now? Call {config.BRAND_PHONE}. Reply STOP to opt out.")


def owner_alert_text(name: str, service: str, phone: str, emergency: bool) -> str:  # sms_owner_alert
    tag = "🚨 EMERGENCY" if emergency else "New lead"
    return f"{tag}: {name} · {service.replace('_',' ')} · {phone}"


def emergency_ack_text() -> str:                               # sms_emergency_ack
    return (f"{config.BRAND}: We received your emergency request — we'll call you "
            f"within 5 minutes. Or call us now: {config.BRAND_PHONE}")


def booking_confirm_text(service: str, when: str) -> str:      # sms_booking_confirm
    return (f"{config.BRAND}: You're booked for {service.replace('_',' ')} on {when}. "
            f"Reply C to confirm. Questions? {config.BRAND_PHONE}")


def quote_ack_text(name: str, service: str) -> str:            # sms_quote_ack
    return (f"{config.BRAND}: Thanks {name}! We're preparing your "
            f"{service.replace('_',' ')} quote and will follow up shortly.")


def review_request_text(name: str, link: str) -> str:          # sms_review
    return (f"{config.BRAND}: Thanks {name}! How did we do? A quick review helps "
            f"a lot: {link} Reply STOP to opt out.")
