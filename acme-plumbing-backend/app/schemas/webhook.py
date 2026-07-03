import uuid
from typing import Optional

from pydantic import BaseModel


class WebhookReceiptResponse(BaseModel):
    """Fast ack for every webhook endpoint. inbox_id is None on duplicates."""

    ok: bool = True
    inbox_id: Optional[uuid.UUID] = None
    duplicate: bool = False
