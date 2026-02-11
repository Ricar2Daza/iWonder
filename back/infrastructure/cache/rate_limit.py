from typing import Optional

import redis

from core.config import settings


def _get_client() -> Optional[redis.Redis]:
    if not settings.REDIS_URL:
        return None
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def is_rate_limited(key: str, limit: int, window_seconds: int) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        count = client.incr(key)
        if count == 1:
            client.expire(key, window_seconds)
        return count > limit
    except Exception:
        return False
