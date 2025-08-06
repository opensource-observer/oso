"""Generic caching utilities for pydantic models

This is a generic set of caching utilities that can be used with any pydantic
model. This allows us to cache many python objects. Rehydration should be done
by the caller but this provides the tools to store and retrieve the objects in
the cache.

We have two kinds of cacheable objects:

1. A single object that can be cached and retrieved
2. A streamable object
"""

import abc
import hashlib
import typing as t
from pathlib import Path

import arrow
from pydantic import BaseModel

T = t.TypeVar("T", bound=BaseModel)


class CacheOptions(BaseModel):
    ttl: int = 0  # Time to live for the cache in seconds. 0 means no expiration.


def key_from_model(model: BaseModel) -> str:
    """Generate a cache key from a pydantic model"""
    return hashlib.sha256(model.model_dump_json().encode()).hexdigest()


class CacheMetadata(BaseModel):
    """Metadata for the cache entry

    This metadata is used to store information about the cache entry such as
    when it was created, when it expires, etc.

    Attributes:
        created_at: The time when the cache entry was created in ISO format.
        valid_until: The time when the cache entry expires in ISO format. If
                    None, the entry only expires if passed in options ttl is
                    exceeded. If it is set, it is always checked against the
                    current time.
    """

    created_at: str  # ISO format timestamp
    valid_until: str | None = None  # ISO format timestamp

    def is_valid(self, options: CacheOptions | None = None) -> bool:
        """Check if the cache entry is valid based on the ttl"""
        created_at = arrow.get(self.created_at)
        now = arrow.now()
        age = created_at - now

        if self.valid_until:
            valid_until = arrow.get(self.valid_until)
            if valid_until < now:
                return False

        if options:
            if options.ttl == 0:
                return True

            if age.total_seconds() > options.ttl:
                return False

        return False  # Placeholder for actual expiration logic


class CacheBackend(abc.ABC):
    """A generic cache backend interface

    This is a generic interface for a cache backend that can be used to store
    and retrieve pydantic models. The actual implementation of the cache backend
    should inherit from this class and implement the methods.
    """

    @abc.abstractmethod
    def store_object(self, key: BaseModel, value: BaseModel) -> None:
        """Store a single object in the cache"""
        ...

    @abc.abstractmethod
    def retrieve_object(
        self,
        key: BaseModel,
        model_type: type[T],
        override_options: CacheOptions | None = None,
    ) -> T:
        """Retrieve a single object from the cache"""
        ...


class FileCacheBackend(CacheBackend):
    """A generic cache for pydantic models"""

    def __init__(self, cache_dir: str, default_options: CacheOptions):
        self.cache_dir = cache_dir
        self.default_options = default_options

    def store_object(self, key: BaseModel, value: BaseModel) -> None:
        """Store a single object in the cache"""
        # Ensure the cache directory exists
        self._ensure_cache_dir()
        # Create a file path based on the key
        file_path = self._cache_key_path(key)

        # Write the value to the file
        with open(file_path, "w") as f:
            f.write(value.model_dump_json())

    def retrieve_object(
        self,
        key: BaseModel,
        model_type: type[T],
        override_options: CacheOptions | None = None,
    ) -> T:
        """Retrieve a single object from the cache"""
        self._ensure_cache_dir()
        file_path = self._cache_key_path(key)
        if not file_path.exists():
            raise FileNotFoundError(f"Cache file not found: {file_path}")

        with open(file_path, "r") as f:
            return model_type.model_validate_json(f.read())

    def _cache_dir_path(self):
        """Get the cache directory path"""
        return Path(self.cache_dir)

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        self._cache_dir_path().mkdir(parents=True, exist_ok=True)

    def _cache_key(self, key: BaseModel) -> str:
        """Generate a cache key from the pydantic model"""
        key_str = hashlib.sha256(key.model_dump_json().encode()).hexdigest()
        return f"{key_str}.json"

    def _cache_key_path(self, key: BaseModel) -> Path:
        """Get the cache file path for a given key"""
        return self._cache_dir_path() / self._cache_key(key)
