"""
Redis-based concurrency store implementation for the scheduler.
"""

import structlog
from oso_core.logging.types import BindableLogger
from redis.asyncio import Redis
from scheduler.types import ConcurrencyLockStore

module_logger = structlog.get_logger(__name__)


class RedisConcurrencyLockStore(ConcurrencyLockStore):
    """Redis-based implementation of the ConcurrencyStore interface."""

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def acquire_lock(
        self, lock_id: str, ttl_seconds: int, log_override: BindableLogger | None = None
    ) -> bool:
        """Acquire a lock for the given key with a timeout."""

        logger = log_override or module_logger

        # Check if the lock is already held
        existing_lock = await self.redis_client.get(name=lock_id)
        logger.debug(
            f"Attempting to acquire lock `{lock_id}`. Existing lock: {existing_lock}"
        )
        if existing_lock is not None:
            return False

        logger.debug(
            f"Lock `{lock_id}` is available. Acquiring with TTL {ttl_seconds} seconds."
        )
        await self.redis_client.set(name=lock_id, value="1", ex=ttl_seconds, nx=True)
        return True

    async def renew_lock(
        self, lock_id: str, ttl_seconds: int, log_override: BindableLogger | None = None
    ) -> bool:
        """Renew a lock for the given lock ID."""
        logger = log_override or module_logger
        logger.debug(
            f"Attempting to renew lock `{lock_id}` with TTL {ttl_seconds} seconds."
        )
        result = await self.redis_client.expire(name=lock_id, time=ttl_seconds)
        return result

    async def release_lock(
        self, lock_id: str, log_override: BindableLogger | None = None
    ) -> None:
        """Release a lock for the given lock ID."""
        logger = log_override or module_logger
        logger.debug(f"Releasing lock `{lock_id}`.")
        await self.redis_client.delete(lock_id)
