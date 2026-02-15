"""
In-memory concurrency lock store for handling message processing without
external locks or coordination.
"""

from scheduler.types import ConcurrencyLockStore


class InMemoryConcurrencyLockStore(ConcurrencyLockStore):
    """In-memory implementation of the ConcurrencyLockStore interface."""

    def __init__(self):
        self.locks = set()

    async def acquire_lock(self, lock_id: str, ttl_seconds: int) -> bool:
        """Acquire a lock for the given key with a timeout."""
        if lock_id in self.locks:
            return False

        self.locks.add(lock_id)
        return True

    async def renew_lock(self, lock_id: str, ttl_seconds: int) -> bool:
        """Renew a lock for the given lock ID."""
        # In-memory locks do not have TTL, so we just check if the lock exists
        return lock_id in self.locks

    async def release_lock(self, lock_id: str) -> None:
        """Release a lock for the given lock ID."""
        self.locks.discard(lock_id)
