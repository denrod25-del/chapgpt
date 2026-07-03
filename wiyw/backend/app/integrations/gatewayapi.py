"""GatewayAPI client — SMS transport only, no business logic. Never raises."""
import logging
from typing import Optional

import httpx

from ..core.config import config

log = logging.getLogger("wiyw.gatewayapi")


async def send_sms(msisdn: str, message: str) -> tuple[bool, Optional[str]]:
    """Send one SMS. msisdn must be E.164 (validated upstream).
    Returns (success, provider_msg_id)."""
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
