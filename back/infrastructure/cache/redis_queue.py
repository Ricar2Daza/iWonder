import json
from typing import Any, Optional

import redis

from core.config import settings


def _get_client() -> Optional[redis.Redis]:
    if not settings.REDIS_URL:
        return None
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def enqueue_job(queue_name: str, payload: dict[str, Any]) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        client.rpush(queue_name, json.dumps(payload))
        return True
    except Exception:
        return False


def dequeue_job(queue_name: str, timeout: int = 5) -> Optional[dict[str, Any]]:
    client = _get_client()
    if not client:
        return None
    try:
        item = client.blpop(queue_name, timeout=timeout)
        if not item:
            return None
        _, raw = item
        return json.loads(raw)
    except Exception:
        return None
