"""
GrokSearchScraper — live web search via xAI Grok API.

Uses Grok's built-in search_parameters to find recent public posts from
Facebook and Instagram pages without requiring Meta API credentials or
browser automation.

How it works:
  1. Receives a source URL (e.g. facebook.com/AlcaldiaTulua) or a plain
     search topic (e.g. "Tuluá servicios públicos").
  2. Sends a structured prompt to grok-2 with search_parameters enabled
     so the model performs a live web search and reads actual page content.
  3. Instructs the model to return a JSON array of individual posts found,
     each with: text, url, date, platform, engagement signals.
  4. Parses and normalises each item into the standard ScrapedItem schema.

Platforms supported via this scraper:
  facebook, instagram, twitter (x), and generic topic searches.

Fallback: if GROK_API_KEY is not set the scraper raises RuntimeError and
the task scheduler falls back to the Playwright scrapers.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import structlog

from app.ingestion.scrapers.base import BaseScraper

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SYSTEM = """\
Eres un extractor de contenido de redes sociales para el sistema de monitoreo \
ciudadano del municipio de Tuluá, Valle del Cauca, Colombia.

Tu tarea: busca publicaciones RECIENTES (últimos 7 días) en la URL o página indicada \
y extrae el contenido textual de cada publicación individual.

Devuelve ÚNICAMENTE un JSON válido con el siguiente formato — sin explicaciones, \
sin markdown, sin texto adicional:

{
  "posts": [
    {
      "text": "<texto completo de la publicación>",
      "url": "<URL directa a la publicación o al perfil si no hay URL individual>",
      "date": "<fecha ISO 8601 o null>",
      "platform": "<facebook|instagram|twitter|news>",
      "likes": <número o null>,
      "comments": <número o null>,
      "shares": <número o null>
    }
  ],
  "source_name": "<nombre de la página o cuenta>",
  "total_found": <número de publicaciones encontradas>
}

Reglas:
- Incluye SOLO publicaciones ciudadanas sobre servicios municipales, obras, \
  seguridad, impuestos, corrupción o gestión pública en Tuluá.
- Excluye publicaciones puramente comerciales o de entretenimiento sin relación \
  con la gestión municipal.
- Si no encuentras publicaciones relevantes, devuelve {"posts": [], "source_name": "", "total_found": 0}.
- El texto de cada publicación debe ser completo, no truncado.
- Máximo 20 publicaciones por llamada.
"""


def _build_user_prompt(url: str, source_name: str, days_back: int = 7) -> str:
    """Build the user message for a specific source URL."""
    since = (datetime.now(tz=timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    return (
        f"Busca y extrae publicaciones recientes desde: {url}\n"
        f"Nombre de la fuente: {source_name}\n"
        f"Periodo: desde {since} hasta hoy.\n"
        f"Incluye publicaciones de ciudadanos o de la alcaldía sobre gestión municipal en Tuluá."
    )


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class GrokSearchScraper(BaseScraper):
    """
    Scraper that uses Grok's live web search to extract social media posts
    without requiring platform API credentials or browser automation.

    Supports any platform whose public pages are indexable by web search
    (Facebook public pages, Instagram public profiles, Twitter/X, news sites).
    """

    platform = "grok_search"

    def __init__(
        self,
        *,
        target_platform: str = "facebook",
        days_back: int = 7,
        max_results: int = 20,
        # BaseScraper kwargs (unused but accepted for interface compatibility)
        proxy_rotation: bool = False,
        proxy_list: Optional[List[str]] = None,
        headless: bool = True,
        timeout_ms: int = 60_000,
    ):
        super().__init__(
            proxy_rotation=proxy_rotation,
            proxy_list=proxy_list,
            headless=headless,
            timeout_ms=timeout_ms,
        )
        self.target_platform = target_platform
        self.days_back = days_back
        self.max_results = max_results

    def _grok_client(self):
        """Return (AsyncOpenAI, model_name) pointing at xAI."""
        from openai import AsyncOpenAI
        from app.config import get_settings

        s = get_settings()
        if not s.grok_api_key:
            raise RuntimeError(
                "GROK_API_KEY is not set. Cannot use GrokSearchScraper."
            )
        return AsyncOpenAI(api_key=s.grok_api_key, base_url="https://api.x.ai/v1"), s.grok_model

    async def _call_grok_search(self, url: str, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Send a live-search request to Grok and parse the JSON response.

        Uses search_parameters.mode="on" so Grok reads current web content.
        Returns the parsed dict or None on failure.
        """
        client, model = self._grok_client()
        since_date = (
            datetime.now(tz=timezone.utc) - timedelta(days=self.days_back)
        ).strftime("%Y-%m-%d")

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": _build_user_prompt(url, source_name, self.days_back)},
                ],
                max_tokens=4000,
                temperature=0.1,
                extra_body={
                    "search_parameters": {
                        "mode": "on",
                        "max_search_results": self.max_results,
                        "from_date": since_date,
                    }
                },
            )
        except Exception as exc:
            logger.error("grok_search_api_error", url=url, error=str(exc))
            return None

        raw = (response.choices[0].message.content or "").strip()

        # Strip markdown fences if the model wraps output despite instructions
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("grok_search_json_parse_failed", url=url, raw_preview=raw[:300])
            return None

    async def _scrape_impl(self, url: Optional[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Scrape a Facebook/Instagram/Twitter page using Grok live search.

        Args:
            url: Public page URL (e.g. https://www.facebook.com/AlcaldiaTulua)
                 or a topic query string.
            kwargs: source_name — human-readable name for the source.
        """
        if not url:
            return []

        source_name: str = kwargs.get("source_name") or _infer_source_name(url)
        log = logger.bind(url=url, source_name=source_name, platform=self.target_platform)
        log.info("grok_search_started")

        data = await self._call_grok_search(url, source_name)
        if not data:
            log.warning("grok_search_no_data")
            return []

        posts = data.get("posts") or []
        if not posts:
            log.info("grok_search_no_posts_found", total=data.get("total_found", 0))
            return []

        resolved_source = data.get("source_name") or source_name
        results: List[Dict[str, Any]] = []

        for post in posts[: self.max_results]:
            text = (post.get("text") or "").strip()
            if not text:
                continue

            post_url = (post.get("url") or url).strip()
            post_date: Optional[datetime] = None

            raw_date = post.get("date")
            if raw_date:
                try:
                    post_date = datetime.fromisoformat(
                        str(raw_date).replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            results.append(
                self._normalize(
                    source=resolved_source,
                    text=text,
                    url=post_url,
                    date=post_date or datetime.now(tz=timezone.utc),
                    metadata={
                        "platform_label": self.target_platform,
                        "likes":    post.get("likes"),
                        "comments": post.get("comments"),
                        "shares":   post.get("shares"),
                        "via":      "grok_live_search",
                    },
                )
            )

        log.info("grok_search_complete", extracted=len(results), total_found=data.get("total_found", 0))
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_source_name(url: str) -> str:
    """Derive a readable source name from a URL."""
    try:
        path = urlparse(url).path.strip("/")
        parts = [p for p in path.split("/") if p and p not in ("groups", "pages")]
        return parts[0] if parts else urlparse(url).netloc
    except Exception:
        return url[:50]
