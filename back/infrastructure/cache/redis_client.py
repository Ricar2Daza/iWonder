import json
from typing import Any, Optional

import redis

from core.config import settings


def get_redis() -> Optional[redis.Redis]:
    if not settings.REDIS_URL:
        return None
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def cache_get_json(key: str) -> Any:
    client = get_redis()
    if not client:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    client = get_redis()
    if not client:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        return


def cache_delete(keys: list[str]) -> None:
    client = get_redis()
    if not client or not keys:
        return
    try:
        client.delete(*keys)
    except Exception:
        return


def cache_delete_prefix(prefix: str) -> None:
    client = get_redis()
    if not client:
        return
    try:
        keys = list(client.scan_iter(match=f"{prefix}*"))
        if keys:
            client.delete(*keys)
    except Exception:
        return
