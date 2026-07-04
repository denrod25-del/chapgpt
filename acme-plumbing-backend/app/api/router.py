"""v1 router aggregation (mounted at settings.API_V1_PREFIX in main.py)."""
from fastapi import APIRouter

from app.api import bookings, events, integrations, leads, reviews, webhooks

api_router = APIRouter()
api_router.include_router(leads.router)
api_router.include_router(bookings.router)
api_router.include_router(events.router)
api_router.include_router(reviews.router)
api_router.include_router(integrations.router)
api_router.include_router(webhooks.router)
