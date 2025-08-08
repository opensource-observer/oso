import hashlib
import logging
import typing as t
from pathlib import Path

import arrow
from pydantic import BaseModel

from .types import (
    CacheBackend,
    CacheInvalidError,
    CacheKey,
    CacheMetadata,
    CacheMetadataOptions,
)

T = t.TypeVar("T", bound=BaseModel)
K = t.TypeVar("K", bound=BaseModel)

logger = logging.getLogger(__name__)


class FileCacheBackend(CacheBackend):
    """A generic cache for pydantic models"""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir

    def store_object(
        self, key: CacheKey, value: BaseModel, options: CacheMetadataOptions
    ) -> None:
        """Store a single object in the cache

        The file cache stores everything as a jsonl file. The first object in
        the file is the metadata, which contains the creation time and
        expiration time of the cache entry.
        """
        # Ensure the cache directory exists
        self._ensure_cache_dir()
        # Create a file path based on the key
        file_path = self._cache_key_path(key)

        metadata = CacheMetadata(
            created_at=arrow.now().isoformat(),
            valid_until=(
                arrow.now().shift(seconds=options.ttl_seconds).isoformat()
                if options.ttl_seconds > 0
                else None
            ),
        )

        # Write the value to the file
        with open(file_path, "w") as f:
            f.write(metadata.model_dump_json() + "\n")
            f.write(value.model_dump_json())

    def retrieve_object(
        self,
        key: CacheKey,
        model_type: type[T],
        options: CacheMetadataOptions,
    ) -> T:
        """Retrieve a single object from the cache"""
        self._ensure_cache_dir()
        file_path = self._cache_key_path(key)

        if not file_path.exists():
            logger.debug(
                f"Cache file not found: {file_path}", extra={"file_path": file_path}
            )
            raise CacheInvalidError(f"Cache file not found: {file_path}")

        with open(file_path, "r") as f:
            # Read the metadata and check if it is valid
            metadata = CacheMetadata.model_validate_json(f.readline().strip())

            if not metadata.is_valid(options):
                logger.debug(
                    f"Cache entry is invalid: {metadata}", extra={"metadata": metadata}
                )
                raise CacheInvalidError(f"Cache entry is invalid: {metadata}")

            return model_type.model_validate_json(f.read())

    def _cache_dir_path(self):
        """Get the cache directory path"""
        return Path(self.cache_dir)

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        self._cache_dir_path().mkdir(parents=True, exist_ok=True)

    def _cache_key(self, key: CacheKey) -> str:
        """Generate a cache key from the pydantic model"""
        key_str = hashlib.sha256(str(key).encode()).hexdigest()
        return f"{key_str}.json"

    def _cache_key_path(self, key: CacheKey) -> Path:
        """Get the cache file path for a given key"""
        return self._cache_dir_path() / self._cache_key(key)
