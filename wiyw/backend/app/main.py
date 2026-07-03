"""WiYW marketing backend — FastAPI entrypoint."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import config
from .models.db import init_pool, close_pool
from .routers import leads, webhooks, events, bookings, quotes_reviews

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate()          # fail fast on missing env
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="WiYW Marketing Backend", version="0.1.0", lifespan=lifespan)
app.include_router(leads.router)
app.include_router(webhooks.router)
app.include_router(events.router)
app.include_router(bookings.bookings_router)
app.include_router(bookings.jobs_router)
app.include_router(quotes_reviews.quotes_router)
app.include_router(quotes_reviews.reviews_router)
app.include_router(quotes_reviews.webhooks_ext)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "brand": config.BRAND}
