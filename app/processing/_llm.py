"""
Shared LLM client for the processing layer.
Supports OpenAI and Grok (x.ai OpenAI-compatible API).
Priority: OpenAI if key present → Grok → RuntimeError.
All classify_* modules import from here to avoid creating a new client per call.
"""
import json
from typing import Any, Dict, Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _make_client():
    """Return (AsyncOpenAI, model_name) for the active provider."""
    from openai import AsyncOpenAI

    s = get_settings()
    if s.openai_api_key:
        return AsyncOpenAI(api_key=s.openai_api_key), s.openai_model
    if s.grok_api_key:
        return (
            AsyncOpenAI(api_key=s.grok_api_key, base_url="https://api.x.ai/v1"),
            s.grok_model,
        )
    raise RuntimeError("No LLM API key configured. Set OPENAI_API_KEY or GROK_API_KEY.")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
async def llm_complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 300,
    temperature: float = 0.0,
) -> str:
    """Single LLM completion with automatic retry on transient errors."""
    client, model = _make_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user[:4000]},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()


async def llm_complete_json(
    system: str,
    user: str,
    *,
    max_tokens: int = 300,
) -> Optional[Dict[str, Any]]:
    """
    LLM completion that parses the response as JSON.
    Strips markdown code fences if the model wraps the output.
    Returns None on parse failure.
    """
    raw = await llm_complete(system, user, max_tokens=max_tokens)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("llm_json_parse_failed", raw=raw[:200])
        return None
