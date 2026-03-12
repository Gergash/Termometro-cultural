"""Topic extraction/classification using LLM."""
from typing import Any, List

from app.config import get_settings


async def extract_topics(text: str) -> List[str]:
    """Extract or classify topics from text (e.g. cultura, educación, seguridad). Returns list of topic strings."""
    if not text or not text.strip():
        return []
    settings = get_settings()
    if settings.openai_api_key:
        return await _openai_topics(text)
    return []


async def _openai_topics(text: str) -> List[str]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=get_settings().openai_api_key)
        response = await client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[
                {"role": "system", "content": "Extrae hasta 5 temas clave del texto en español (Tuluá, municipio). Responde solo con temas separados por coma."},
                {"role": "user", "content": text[:4000]},
            ],
            max_tokens=100,
        )
        raw = (response.choices[0].message.content or "").strip()
        return [t.strip() for t in raw.split(",") if t.strip()][:5]
    except Exception:
        return []
