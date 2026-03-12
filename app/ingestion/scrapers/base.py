"""
Base scraper interface for the Social Sentiment Monitoring System.
All platform scrapers must implement this interface and return normalized ScrapedItem objects.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.ingestion.schemas import ScrapedItem


class BaseScraper(ABC):
    """
    Abstract base class for social and news scrapers.
    Subclasses must implement scrape() and return a list of ScrapedItem (or dicts matching that schema).
    """

    platform: str = ""

    def __init__(
        self,
        *,
        proxy_rotation: bool = False,
        proxy_list: Optional[List[str]] = None,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ):
        self.proxy_rotation = proxy_rotation
        self.proxy_list = proxy_list or []
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._proxy_index = 0

    def _next_proxy(self) -> Optional[str]:
        """Return next proxy URL when rotation is enabled."""
        if not self.proxy_rotation or not self.proxy_list:
            return None
        proxy = self.proxy_list[self._proxy_index % len(self.proxy_list)]
        self._proxy_index += 1
        return proxy

    def _normalize(
        self,
        source: str,
        text: str,
        url: str,
        date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build normalized output schema for a single item."""
        return {
            "source": source,
            "platform": self.platform,
            "text": text or "",
            "date": date,
            "url": url or "",
            "metadata": metadata or {},
        }

    def _to_scraped_items(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert list of raw dicts to normalized schema (JSON-ready)."""
        return [
            self._normalize(
                source=item.get("source", ""),
                text=item.get("text", ""),
                url=item.get("url", ""),
                date=item.get("date"),
                metadata=item.get("metadata", {}),
            )
            for item in raw_items
        ]

    @abstractmethod
    async def scrape(self, url: Optional[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Perform the scrape and return a list of normalized items.
        Each item must have: source, platform, text, date, url, metadata.
        """
        pass
