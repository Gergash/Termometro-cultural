"""FastAPI application for Termómetro Cultural."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import posts, sentiment, health
from app.config import get_settings
from app.storage.database import engine, Base
from app.storage.models import Post  # noqa: F401 - register models with Base for create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if needed (for dev; use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Termómetro Cultural API",
    description="Social Sentiment Monitoring for Tuluá – posts, sentiment, topics",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])


@app.get("/")
async def root():
    return {"service": "termometro-cultural", "docs": "/docs"}
