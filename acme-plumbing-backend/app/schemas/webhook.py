import uuid
from typing import Optional

from pydantic import BaseModel


class WebhookReceiptResponse(BaseModel):
    """Fast, predictable ack for every webhook endpoint.

    - `inbox_id` is None on duplicates (already-seen provider re-delivery).
    - `verification_status`: pending | verified | unverified | invalid | unconfigured
    - `processing_status`: received | processed | failed | skipped (None if not processed inline)
    """

    ok: bool = True
    duplicate: bool = False
    inbox_id: Optional[uuid.UUID] = None
    event_type: Optional[str] = None
    verification_status: str = "pending"
    processing_status: Optional[str] = None
    applied: int = 0                      # number of events reconciled into the DB
