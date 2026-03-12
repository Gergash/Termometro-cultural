"""Sentiment and topics aggregates for dashboards."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_db
from app.storage.models.post import Post

router = APIRouter()


@router.get("/summary")
async def sentiment_summary(
    platform: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate sentiment counts (positive, negative, neutral) for dashboard."""
    q = select(Post.sentiment_label, func.count(Post.id)).where(Post.sentiment_label.isnot(None)).group_by(Post.sentiment_label)
    if platform:
        q = q.where(Post.platform == platform)
    result = await db.execute(q)
    rows = result.all()
    return {"by_label": {r[0]: r[1] for r in rows}}
