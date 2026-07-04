"""Import every model so Base.metadata is fully populated (Alembic target)."""
from app.models.base import Base
from app.models.booking import Booking
from app.models.brand import Brand
from app.models.communication_log import CommunicationLog
from app.models.contact import Contact
from app.models.event_log import EventLog
from app.models.lead import Lead
from app.models.webhook_inbox import WebhookInbox

__all__ = [
    "Base",
    "Brand",
    "Contact",
    "Lead",
    "Booking",
    "EventLog",
    "WebhookInbox",
    "CommunicationLog",
]
