"""Global daily usage counter for capping OpenAI spend on the public demo.

Backed by Redis so the cap is shared across service replicas. Fails open: if
Redis is unavailable or unconfigured, requests are allowed through.
"""

import logging
import os
from datetime import date

logger = logging.getLogger(__name__)

_client = None


def _redis():
    global _client
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    if _client is None:
        import redis

        _client = redis.from_url(url)
    return _client


def llm_usage() -> dict:
    """Read today's global LLM call count without incrementing.

    Powers the in-app System status page. Mirrors the key/limit used by
    ``llm_budget_exceeded`` so the number shown matches what gates requests.
    """
    limit = int(os.getenv("OPENAI_DAILY_LIMIT", "500"))
    client = _redis()
    if client is None:
        return {"used": 0, "limit": limit, "enabled": False}

    key = f"llm:calls:{date.today().isoformat()}"
    try:
        used = int(client.get(key) or 0)
    except Exception:
        logger.warning("redis usage read failed", exc_info=True)
        return {"used": 0, "limit": limit, "enabled": False}
    return {"used": used, "limit": limit, "enabled": True}


def llm_budget_exceeded() -> bool:
    """Increment today's global LLM call counter and report whether the cap is hit."""
    client = _redis()
    if client is None:
        return False

    limit = int(os.getenv("OPENAI_DAILY_LIMIT", "500"))
    key = f"llm:calls:{date.today().isoformat()}"
    try:
        count = client.incr(key)
        if count == 1:
            client.expire(key, 172800)
        return count > limit
    except Exception:
        logger.warning("redis usage check failed; allowing request", exc_info=True)
        return False
