"""Alembic import target.

Importing this module pulls in Base *and* every model, so Base.metadata is
complete. Alembic's env.py imports `target_metadata` from here.
"""
from app.models import Base  # noqa: F401  (re-exported)
from app.models import (  # noqa: F401  (registers tables on Base.metadata)
    Booking,
    Brand,
    CommunicationLog,
    Contact,
    EventLog,
    Lead,
    WebhookInbox,
)

target_metadata = Base.metadata
