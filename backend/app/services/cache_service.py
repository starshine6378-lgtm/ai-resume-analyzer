import asyncio
import json
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ImportError:  # Optional until REDIS_URL is configured.
    Redis = None  # type: ignore[assignment,misc]

    class RedisError(Exception):
        pass

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    value: str
    expires_at: float


class CacheService:
    """Redis-first JSON cache with a process-local fallback.

    Redis errors never break the resume analysis path. This is intentional:
    caching is an optimization, not a business dependency.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        if redis_url and Redis is None:
            logger.warning("REDIS_URL is configured but the redis package is unavailable")
        self._redis = (
            Redis.from_url(redis_url, decode_responses=True)
            if redis_url and Redis is not None
            else None
        )
        self._memory: dict[str, MemoryItem] = {}
        self._lock = asyncio.Lock()

    @property
    def backend_name(self) -> str:
        return "redis+memory-fallback" if self._redis else "memory"

    async def get_json(self, key: str) -> dict[str, Any] | None:
        if self._redis:
            try:
                raw = await self._redis.get(key)
                if raw:
                    return json.loads(raw)
            except (RedisError, json.JSONDecodeError) as exc:
                logger.warning("Redis get failed; using memory fallback: %s", exc)

        async with self._lock:
            item = self._memory.get(key)
            if not item:
                return None
            if item.expires_at <= time.monotonic():
                self._memory.pop(key, None)
                return None
            try:
                return json.loads(item.value)
            except json.JSONDecodeError:
                self._memory.pop(key, None)
                return None

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))

        if self._redis:
            try:
                await self._redis.setex(key, ttl_seconds, raw)
            except RedisError as exc:
                logger.warning("Redis set failed; using memory fallback: %s", exc)

        async with self._lock:
            self._memory[key] = MemoryItem(
                value=raw,
                expires_at=time.monotonic() + ttl_seconds,
            )
            if len(self._memory) > 500:
                now = time.monotonic()
                expired = [key for key, item in self._memory.items() if item.expires_at <= now]
                for expired_key in expired:
                    self._memory.pop(expired_key, None)

    async def delete(self, key: str) -> None:
        if self._redis:
            try:
                await self._redis.delete(key)
            except RedisError as exc:
                logger.warning("Redis delete failed: %s", exc)
        async with self._lock:
            self._memory.pop(key, None)

    async def ping(self) -> bool:
        if not self._redis:
            return True
        try:
            return bool(await self._redis.ping())
        except RedisError:
            return False

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()


@lru_cache
def get_cache_service() -> CacheService:
    return CacheService(get_settings().redis_url)
