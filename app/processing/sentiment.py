"""Sentiment classification using OpenAI (or Grok)."""
from typing import Any, Dict

from app.config import get_settings


async def classify_sentiment(text: str) -> Dict[str, Any]:
    """
    Classify sentiment of text. Returns {score, label}.
    Uses OpenAI by default; can be switched to Grok via config.
    """
    if not text or not text.strip():
        return {"score": "neutral", "label": "Neutral"}
    settings = get_settings()
    if settings.openai_api_key:
        return await _openai_sentiment(text, settings.openai_model)
    return {"score": "neutral", "label": "Neutral (no API key)"}


async def _openai_sentiment(text: str, model: str) -> Dict[str, Any]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=get_settings().openai_api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Clasifica el sentimiento del texto en español: positive, negative, neutral. Responde solo con una palabra."},
                {"role": "user", "content": text[:4000]},
            ],
            max_tokens=10,
        )
        label = (response.choices[0].message.content or "neutral").strip().lower()
        if "pos" in label:
            return {"score": "positive", "label": "Positive"}
        if "neg" in label:
            return {"score": "negative", "label": "Negative"}
        return {"score": "neutral", "label": "Neutral"}
    except Exception:
        return {"score": "neutral", "label": "Neutral (error)"}
