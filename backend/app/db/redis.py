"""Redis 客户端：不可用时自动降级为进程内内存存储，避免本地无 Redis 导致接口 500。"""
import logging
import time

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryRedis:
    """极简内存实现，覆盖本项目用到的 get/set/delete/incr 操作。"""

    def __init__(self):
        self._store: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def set(self, key, value, *args, **kwargs) -> bool:
        self._store[str(key)] = str(value)
        return True

    def get(self, key):
        return self._store.get(str(key))

    def delete(self, key) -> bool:
        return self._store.pop(str(key), None) is not None

    def exists(self, key) -> bool:
        return str(key) in self._store

    def incr(self, key, amount: int = 1) -> int:
        value = int(self._store.get(str(key), 0)) + amount
        self._store[str(key)] = str(value)
        return value

    def decr(self, key, amount: int = 1) -> int:
        return self.incr(key, -amount)


_pool = None
_fallback = MemoryRedis()
_next_retry = 0.0


def get_redis():
    """FastAPI 依赖：优先真实 Redis，失败时返回内存降级客户端。"""
    global _pool, _next_retry

    if not settings.REDIS_ENABLED:
        return _fallback
    if time.time() < _next_retry:
        return _fallback

    try:
        if _pool is None:
            _pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        client = redis.Redis(connection_pool=_pool)
        client.ping()
        return client
    except Exception:
        _next_retry = time.time() + 30
        logger.warning("Redis 不可用，已切换为内存模式（30秒后重试）")
        return _fallback
