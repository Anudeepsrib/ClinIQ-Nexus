"""Redis-backed rate limiting."""

from __future__ import annotations

import time
from typing import Tuple

from app.core.cache import get_redis


async def check_rate_limit(
    key: str, limit: int, window: int = 60
) -> Tuple[bool, int, int]:
    """
    Returns (allowed, remaining, reset_seconds).
    Uses a simple sliding window counter in Redis.
    """
    redis = await get_redis()
    now = int(time.time())
    window_key = f"{key}:{now // window}"

    pipe = redis.pipeline()
    pipe.incr(window_key)
    pipe.expire(window_key, window + 1)
    results = await pipe.execute()

    count = int(results[0])
    remaining = max(0, limit - count)
    reset = window - (now % window)

    return count <= limit, remaining, reset
