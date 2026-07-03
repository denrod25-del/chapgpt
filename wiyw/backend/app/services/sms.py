"""SMS via GatewayAPI. Returns (success, provider_msg_id)."""
import logging
from typing import Optional
import httpx
from ..config import config

log = logging.getLogger("wiyw.sms")


async def send_sms(msisdn: str, message: str) -> tuple[bool, Optional[str]]:
    """Send one SMS. msisdn must be E.164 (validated upstream). Never raises."""
    if not (config.GATEWAYAPI_TOKEN and msisdn and message):
        return False, None
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://gatewayapi.com/rest/mtsms",
                auth=(config.GATEWAYAPI_TOKEN, ""),
                json={"sender": config.GATEWAYAPI_SENDER,
                      "message": message,
                      "recipients": [{"msisdn": int(msisdn.lstrip("+"))}]},
            )
        if r.status_code < 300:
            body = r.json()
            ids = body.get("ids") or []
            return True, str(ids[0]) if ids else None
        log.error("GatewayAPI %s: %s", r.status_code, r.text[:200])
        return False, None
    except (httpx.HTTPError, ValueError) as e:
        log.error("GatewayAPI transport error: %s", e)
        return False, None


def lead_confirm_text(name: str) -> str:
    return (f"{config.BRAND}: Thanks {name}! We got your request and will call "
            f"you shortly. Need us now? Call {config.BRAND_PHONE}. Reply STOP to opt out.")


def owner_alert_text(name: str, service: str, phone: str, emergency: bool) -> str:
    tag = "🚨 EMERGENCY" if emergency else "New lead"
    return f"{tag}: {name} · {service.replace('_',' ')} · {phone}"
