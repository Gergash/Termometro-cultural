"""Post and source models for scraped content and NLP results."""
from sqlalchemy import Boolean, Column, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.storage.database import Base


class ScrapedSource(Base):
    """Registered source (page, profile, site) for ingestion."""
    __tablename__ = "scraped_sources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(32), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Post(Base):
    """Single scraped item (post/tweet/article) with optional NLP results."""
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_platform_posted", "platform", "posted_at"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(255), nullable=False, index=True)
    platform = Column(String(32), nullable=False, index=True)
    text = Column(Text, nullable=False)
    url = Column(String(2048), nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_ = Column("metadata", JSON, default=dict)
    sentiment_score = Column(String(32), nullable=True, index=True)
    sentiment_label = Column(String(64), nullable=True)
    topics = Column(JSON, default=list)
