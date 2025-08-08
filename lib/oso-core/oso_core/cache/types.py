"""Caching utilities for pydantic models

Types used to describe a set of caching utilities that can be used with any
pydantic model. This allows us to cache many python objects.
"""

import abc
import typing as t

import arrow
import orjson
from pydantic import BaseModel

T = t.TypeVar("T", bound=BaseModel)
K = t.TypeVar("K", bound=BaseModel)


class CacheMetadataOptions(BaseModel):
    ttl_seconds: int = (
       900  # Time to live for the cache in seconds. 0 means no expiration.
    )
    override_ttl: bool = False


class CacheOptions(BaseModel):
    """Options for the cache backend

    Attributes:
        ttl_seconds: Default time to live for the cache in seconds. 0 means no expiration.
    """

    default_ttl_seconds: int = (
        900  # Time to live for the cache in seconds. 0 means no expiration.
    )
    enabled: bool = True  # Whether the cache is enabled


class CompositeCacheKey(t.Protocol):
    def __str__(self) -> str:
        """Return a string representation of the cache key."""
        ...


class MultiStringCacheKey:
    """A cache key that is a combination of multiple strings."""

    def __init__(self, *args: str):
        self._key = "_".join(args)

    def __str__(self) -> str:
        return self._key

    def __repr__(self) -> str:
        return f"MultiStringCacheKey({self._key})"


class StructuredCacheKey(BaseModel):
    """A cache key that is a structured object.

    This allows us to use any pydantic model as a cache key.
    """

    def __str__(self) -> str:
        return orjson.dumps(self.model_dump(), option=orjson.OPT_SORT_KEYS).decode(
            "utf-8"
        )


CacheKey = t.Union[str, CompositeCacheKey]


class NotFoundError(Exception):
    pass


class CacheInvalidError(Exception):
    pass


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

    def is_valid(self, options: CacheMetadataOptions | None = None) -> bool:
        """Check if the cache entry is valid based on the ttl"""
        created_at = arrow.get(self.created_at)
        now = arrow.now()
        age = created_at - now

        if self.valid_until:
            valid_until = arrow.get(self.valid_until)
            if valid_until < now:
                return False

        if options:
            if options.override_ttl:
                if options.ttl_seconds == 0:
                    return True

                if age.total_seconds() > options.ttl_seconds:
                    return False

        return True


class CacheBackend(abc.ABC):
    """A generic cache backend interface

    This is a generic interface for a cache backend that can be used to store
    and retrieve pydantic models. The actual implementation of the cache backend
    should inherit from this class and implement the methods.
    """

    @abc.abstractmethod
    def store_object(
        self, key: CacheKey, value: BaseModel, options: CacheMetadataOptions
    ) -> None:
        """Store a single object in the cache"""
        ...

    @abc.abstractmethod
    def retrieve_object(
        self,
        key: CacheKey,
        model_type: type[T],
        options: CacheMetadataOptions,
    ) -> T:
        """Retrieve a single object from the cache"""
        ...


class Cache:
    @classmethod
    def from_backend(cls, backend: CacheBackend, options: CacheOptions) -> "Cache":
        """Create a Cache instance from a CacheBackend"""
        return cls(backend=backend, options=options)

    def __init__(self, backend: CacheBackend, options: CacheOptions):
        self.backend = backend
        self.options = options

    def store_object(
        self,
        key: CacheKey,
        value: BaseModel,
        options: CacheMetadataOptions | None = None,
    ) -> None:
        """Store a single object in the cache"""
        if not self.options.enabled:
            return
        self.backend.store_object(
            key,
            value,
            options
            or CacheMetadataOptions(ttl_seconds=self.options.default_ttl_seconds),
        )

    def retrieve_object(
        self,
        key: CacheKey,
        model_type: type[T],
        options: CacheMetadataOptions | None = None,
    ) -> T:
        """Retrieve a single object from the cache"""
        if not self.options.enabled:
            raise CacheInvalidError("Cache is not enabled")

        return self.backend.retrieve_object(
            key,
            model_type,
            options
            or CacheMetadataOptions(ttl_seconds=self.options.default_ttl_seconds),
        )
