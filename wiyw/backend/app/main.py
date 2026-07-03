"""WiYW marketing backend — FastAPI entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import api_router
from .core.config import config
from .db.session import close_pool, init_pool

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate()          # fail fast on missing env
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="WiYW Marketing Backend", version="1.0.0", lifespan=lifespan)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["content-type", "idempotency-key"],
    )

# Versioned contract + legacy unprefixed paths during the frontend transition.
# Drop the legacy mount once the site and all provider webhook URLs use /api/v1.
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, include_in_schema=False)
