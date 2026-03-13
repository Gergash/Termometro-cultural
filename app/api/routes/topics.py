"""
GET /api/topics/trending
Most discussed municipal topics with sentiment and urgency breakdown.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.aggregates import get_trending_topics
from app.api.dependencies import CommonFilters, get_db
from app.api.schemas import MetaResponse, TopicsTrendingResponse

router = APIRouter()


@router.get(
    "/trending",
    response_model=TopicsTrendingResponse,
    summary="Trending topics",
    description=(
        "Returns the most discussed municipal topics ranked by post count. "
        "Each entry includes sentiment breakdown (positive/neutral/negative) "
        "and count of high-urgency posts. Filterable by date range and platform."
    ),
)
async def trending_topics(
    limit: int = Query(10, ge=1, le=50, description="Max number of topics to return."),
    filters: CommonFilters = Depends(),
    db: AsyncSession = Depends(get_db),
):
    data = await get_trending_topics(db, filters, limit=limit)
    return TopicsTrendingResponse(
        topics=data["topics"],
        total_classified=data["total_classified"],
        meta=MetaResponse(
            generated_at=datetime.now(tz=timezone.utc),
            filters_applied=filters.as_dict(),
        ),
    )
