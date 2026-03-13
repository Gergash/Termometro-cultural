"""
Response schemas for the analytics API.
All endpoints use these Pydantic models so FastAPI generates accurate OpenAPI docs.
"""
from datetime import date, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Shared wrappers
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int = Field(..., description="Total matching records (before pagination)")
    page: int
    page_size: int
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def build(cls, data: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        import math
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if page_size else 1,
        )


class MetaResponse(BaseModel):
    """Envelope with metadata for non-paginated endpoints."""
    generated_at: datetime
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# GET /sentiment/summary
# ---------------------------------------------------------------------------

class SentimentBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0
    score: float = Field(
        0.0,
        description="Net sentiment score: (positive − negative) / total. Range −1 to 1.",
        ge=-1.0,
        le=1.0,
    )
    positive_pct: float = Field(0.0, description="% positive posts")
    negative_pct: float = Field(0.0, description="% negative posts")
    neutral_pct: float = Field(0.0, description="% neutral posts")


class SentimentSummaryResponse(BaseModel):
    summary: SentimentBreakdown
    by_platform: Dict[str, SentimentBreakdown] = Field(
        default_factory=dict,
        description="Sentiment breakdown per platform",
    )
    meta: MetaResponse


# ---------------------------------------------------------------------------
# GET /topics/trending
# ---------------------------------------------------------------------------

class TopicTrend(BaseModel):
    slug: str = Field(..., description="Topic identifier, e.g. 'infrastructure'")
    name: str
    count: int = Field(..., description="Number of posts classified under this topic")
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    urgency_high: int = Field(0, description="Posts with high urgency in this topic")
    share_pct: float = Field(0.0, description="Percentage of total classified posts")


class TopicsTrendingResponse(BaseModel):
    topics: List[TopicTrend]
    total_classified: int = Field(..., description="Total posts with a topic assigned")
    meta: MetaResponse


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------

class AlertItem(BaseModel):
    id: int
    text: str = Field(..., description="First 400 chars of post text")
    platform: str
    source_name: Optional[str] = None
    url: str
    posted_at: Optional[datetime] = None
    urgency: str
    sentiment: str
    confidence: Optional[float] = None
    topic: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /timeline
# ---------------------------------------------------------------------------

class TimelinePoint(BaseModel):
    date: date
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0
    score: float = Field(0.0, description="Net sentiment score for this day")
    avg_confidence: Optional[float] = None


class TimelineResponse(BaseModel):
    timeline: List[TimelinePoint]
    meta: MetaResponse


# ---------------------------------------------------------------------------
# GET /sources
# ---------------------------------------------------------------------------

class SourceEngagement(BaseModel):
    source_id: int
    name: str
    platform: str
    post_count: int
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    high_urgency: int = Field(0, description="Posts with high urgency")
    avg_confidence: Optional[float] = None
    score: float = Field(0.0, description="Net sentiment score for this source")
    last_scraped_at: Optional[datetime] = None
