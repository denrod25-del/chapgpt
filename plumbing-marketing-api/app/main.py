"""Plumbing Marketing API — FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG, lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
