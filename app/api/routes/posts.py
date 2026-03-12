"""Posts API: list and filter scraped content."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_db
from app.storage.models.post import Post

router = APIRouter()


@router.get("")
async def list_posts(
    platform: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List posts with optional filters."""
    q = select(Post).order_by(Post.scraped_at.desc()).limit(limit)
    if platform:
        q = q.where(Post.platform == platform)
    if source:
        q = q.where(Post.source == source)
    if from_date:
        q = q.where(Post.posted_at >= from_date)
    if to_date:
        q = q.where(Post.posted_at <= to_date)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [{"id": r.id, "source": r.source, "platform": r.platform, "text": r.text[:500], "url": r.url, "posted_at": r.posted_at, "sentiment_label": r.sentiment_label} for r in rows]
