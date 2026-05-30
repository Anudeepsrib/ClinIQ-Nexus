"""Redis client singleton."""

from __future__ import annotations

import redis.asyncio as redis
from functools import lru_cache

from app.core.config import settings


@lru_cache
def _get_redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> redis.Redis:
    return _get_redis_client()
