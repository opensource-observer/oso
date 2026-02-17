"""
Redis-based concurrency store implementation for the scheduler.
"""

from redis.asyncio import Redis
from scheduler.types import ConcurrencyLockStore


class RedisConcurrencyLockStore(ConcurrencyLockStore):
    """Redis-based implementation of the ConcurrencyStore interface."""

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def acquire_lock(self, lock_id: str, ttl_seconds: int) -> bool:
        """Acquire a lock for the given key with a timeout."""

        # Check if the lock is already held
        existing_lock = await self.redis_client.get(name=lock_id)
        if existing_lock is not None:
            return False

        await self.redis_client.set(name=lock_id, value="1", ex=ttl_seconds, nx=True)
        return True

    async def renew_lock(self, lock_id: str, ttl_seconds: int) -> bool:
        """Renew a lock for the given lock ID."""
        result = await self.redis_client.expire(name=lock_id, time=ttl_seconds)
        return result

    async def release_lock(self, lock_id: str) -> None:
        """Release a lock for the given lock ID."""
        await self.redis_client.delete(lock_id)
