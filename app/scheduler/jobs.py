"""Scheduled jobs: run scrapers and processing pipeline. Integrate with Celery or APScheduler."""
from typing import Any, Dict, List, Optional

# Example: run scrapers for configured sources and then run pipeline on new items.
# In production, use Celery beat or APScheduler to call these.


async def run_ingestion_job(sources: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Run ingestion for given sources (or default list).
    Each source: {url, platform, name}. Returns list of scraped items.
    """
    from app.ingestion.scrapers import FacebookScraper, InstagramScraper, TwitterScraper, NewsScraper

    if not sources:
        sources = []
    all_items: List[Dict[str, Any]] = []
    for s in sources:
        url = s.get("url")
        platform = (s.get("platform") or "").lower()
        if not url:
            continue
        if platform in ("facebook", "facebook_group"):
            scraper = FacebookScraper()
        elif platform == "instagram":
            scraper = InstagramScraper()
        elif platform == "twitter":
            scraper = TwitterScraper()
        elif platform == "news":
            scraper = NewsScraper()
        else:
            continue
        items = await scraper.scrape(url=url)
        for it in items:
            it["source"] = it.get("source") or s.get("name", "")
        all_items.extend(items)
    return all_items


async def run_processing_job(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run NLP pipeline on items. Returns items with sentiment and topics."""
    from app.processing.pipeline import run_pipeline
    return await run_pipeline(items)
