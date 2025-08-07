"""Caching utilities for pydantic models

Types used to describe a set of caching utilities that can be used with any
pydantic model. This allows us to cache many python objects.
"""

import abc
import typing as t

import arrow
from pydantic import BaseModel

T = t.TypeVar("T", bound=BaseModel)
K = t.TypeVar("K", bound=BaseModel)


class CacheOptions(BaseModel):
    ttl: int = 0  # Time to live for the cache in seconds. 0 means no expiration.


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
    def store_object(
        self, key: str, value: BaseModel, override_options: CacheOptions | None = None
    ) -> None:
        """Store a single object in the cache"""
        ...

    @abc.abstractmethod
    def retrieve_object(
        self,
        key: str,
        model_type: type[T],
        override_options: CacheOptions | None = None,
    ) -> T:
        """Retrieve a single object from the cache"""
        ...
