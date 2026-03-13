"""
FastAPI application for Termómetro Cultural.
Registers all routers and configures CORS, OpenAPI metadata and lifespan.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, posts, sentiment, topics, alerts, timeline, sources, webhooks
from app.config import get_settings
from app.storage.database import engine, Base
from app.storage.models import *  # noqa: F401, F403 — register all models with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Termómetro Cultural API",
    description=(
        "Social Sentiment Monitoring for Tuluá, Valle del Cauca — 2024-2027.\n\n"
        "Monitors citizen opinions from Facebook, Instagram, X and local news. "
        "Classifies sentiment (positive/neutral/negative), topic "
        "(security, taxes, public_services, infrastructure, corruption, public_administration, other) "
        "and urgency (low/medium/high) using LLMs.\n\n"
        "**Analytics endpoints:**\n"
        "- `/api/sentiment/summary` — net sentiment score\n"
        "- `/api/topics/trending` — most discussed topics\n"
        "- `/api/alerts` — high-urgency negative posts\n"
        "- `/api/timeline` — sentiment over time\n"
        "- `/api/sources` — engagement by source\n\n"
        "**Webhook endpoints (n8n / GPT / Telegram):**\n"
        "- `POST /webhooks/trigger-scraping` — dispatch scraping job\n"
        "- `POST /webhooks/generate-report` — generate custom period report\n"
        "- `GET /webhooks/latest-alerts` — latest critical alerts (formatted)\n"
        "- `GET /webhooks/weekly-thermometer` — full weekly report (formatted)\n"
    ),
    version="1.2.0",
    contact={"name": "Municipio de Tuluá", "email": "sistemas@tulua.gov.co"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core
app.include_router(health.router,    prefix="/health",             tags=["health"])
app.include_router(posts.router,     prefix="/api/posts",          tags=["posts"])

# Analytics
app.include_router(sentiment.router, prefix="/api/sentiment",      tags=["sentiment"])
app.include_router(topics.router,    prefix="/api/topics",         tags=["topics"])
app.include_router(alerts.router,    prefix="/api/alerts",         tags=["alerts"])
app.include_router(timeline.router,  prefix="/api/timeline",       tags=["timeline"])
app.include_router(sources.router,   prefix="/api/sources",        tags=["sources"])

# Webhooks (n8n / Custom GPT / Telegram)
app.include_router(webhooks.router,  prefix="/webhooks",           tags=["webhooks"])


@app.get("/", tags=["root"], summary="Service info")
async def root():
    return {
        "service":     "termometro-cultural",
        "version":     "1.2.0",
        "municipality": settings.municipality_name,
        "docs":        "/docs",
        "redoc":       "/redoc",
    }
