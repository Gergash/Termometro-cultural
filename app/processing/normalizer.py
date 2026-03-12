"""Text normalization for NLP: cleanup, lowercase, truncation."""
import re
from typing import Optional


def normalize_text(text: str, max_chars: Optional[int] = 8000) -> str:
    """Clean and normalize text for sentiment/topic models."""
    if not text or not isinstance(text, str):
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    if max_chars and len(t) > max_chars:
        t = t[:max_chars].rsplit(" ", 1)[0] + " "
    return t.strip()
