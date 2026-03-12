"""Aggregation helpers for trends and distributions."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.posts import Post


async def sentiment_by_date(
    db: AsyncSession,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Daily sentiment counts for trend charts."""
    q = select(
        func.date(Post.posted_at).label("day"),
        Post.cached_sentiment_label,
        func.count(Post.id).label("count"),
    ).where(Post.cached_sentiment_label.isnot(None), Post.posted_at.isnot(None))
    if from_date:
        q = q.where(Post.posted_at >= from_date)
    if to_date:
        q = q.where(Post.posted_at <= to_date)
    if platform:
        q = q.where(Post.platform == platform)
    q = q.group_by(func.date(Post.posted_at), Post.cached_sentiment_label)
    result = await db.execute(q)
    return [{"day": str(r.day), "sentiment": r.cached_sentiment_label, "count": r.count} for r in result.all()]
