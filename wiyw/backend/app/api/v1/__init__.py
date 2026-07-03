"""API v1 router aggregation. main.py mounts this once at '' (legacy paths) and
once at '/api/v1' (versioned contract) during the transition."""
from fastapi import APIRouter

from ...webhooks.routes import router as webhooks_router
from . import bookings, dashboard, events, health, integrations, leads, quotes, reviews

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(leads.router)
api_router.include_router(quotes.router)
api_router.include_router(bookings.bookings_router)
api_router.include_router(bookings.jobs_router)
api_router.include_router(reviews.router)
api_router.include_router(events.router)
api_router.include_router(integrations.router)
api_router.include_router(dashboard.router)
api_router.include_router(webhooks_router)
