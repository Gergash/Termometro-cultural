"""NLP pipeline: normalize text -> sentiment -> topics. Placeholder for LLM integration."""
from typing import Any, Dict, List

from app.processing.normalizer import normalize_text
from app.processing.sentiment import classify_sentiment
from app.processing.topics import extract_topics


async def run_pipeline(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run full pipeline on scraped items: normalize text, classify sentiment, extract topics.
    Returns same list with added keys: normalized_text, sentiment_score, sentiment_label, topics.
    """
    results = []
    for item in items:
        text = item.get("text") or ""
        normalized = normalize_text(text)
        sentiment = await classify_sentiment(normalized)
        topics_list = await extract_topics(normalized)
        out = {**item, "normalized_text": normalized}
        out["sentiment_score"] = sentiment.get("score")
        out["sentiment_label"] = sentiment.get("label")
        out["topics"] = topics_list
        results.append(out)
    return results
