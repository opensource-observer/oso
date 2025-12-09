import functools
import hashlib
import pickle
from typing import Any, Callable, Optional, TypeVar
from urllib.parse import urlparse

from dagster import AssetExecutionContext
from redis import Redis

R = TypeVar("R")


def redis_cache(
    context: AssetExecutionContext,
    http_cache: Optional[str],
    func: Callable[..., R],
    ttl: int = 86400,
) -> Callable[..., R]:
    """
    A Redis-based cache decorator that works as a drop-in replacement for @cache.

    Args:
        context: Dagster execution context for logging
        http_cache: Redis URL for caching (if None, no caching is performed)
        func: Function to be cached
        ttl: Time-to-live for cached results in seconds (default: 1 day)

    Returns:
        Wrapped function with Redis caching

    Falls back to no caching if Redis is not available or configured.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        redis_client = None
        func_name = f"{func.__module__}.{func.__qualname__}"

        if not http_cache:
            context.log.debug(
                f"Redis cache disabled for {func_name}: no http_cache URL provided"
            )
            return func(*args, **kwargs)

        context.log.debug(f"Redis cache attempting to connect for {func_name}")
        try:
            parsed_url = urlparse(http_cache)
            redis_client = Redis(
                host=parsed_url.hostname or "localhost",
                port=parsed_url.port or 6379,
                password=parsed_url.password,
                username=parsed_url.username,
                decode_responses=False,
            )
            redis_client.ping()
            context.log.debug(
                f"Redis cache connection established for {func_name} at {parsed_url.hostname}:{parsed_url.port or 6379}"
            )
        except Exception as e:
            context.log.warning(
                f"Redis cache connection failed for {func_name}: {str(e)}, falling back to no caching"
            )
            redis_client = None

        if not redis_client:
            return func(*args, **kwargs)

        try:
            key_data = (
                func.__module__,
                func.__qualname__,
                args,
                tuple(sorted(kwargs.items())),
            )
            cache_key = (
                f"redis_cache:{hashlib.sha256(pickle.dumps(key_data)).hexdigest()}"
            )
            context.log.debug(f"Redis cache key generated for {func_name}: {cache_key}")
        except Exception as e:
            context.log.warning(
                f"Failed to generate SHA256 cache key for {func_name}: {str(e)}, using MD5 fallback"
            )
            key_parts = [func.__module__, func.__qualname__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = (
                f"redis_cache:{hashlib.md5('|'.join(key_parts).encode()).hexdigest()}"
            )
            context.log.debug(f"MD5 fallback cache key for {func_name}: {cache_key}")

        try:
            cached_result = redis_client.get(cache_key)
            if cached_result is not None and isinstance(cached_result, bytes):
                context.log.info(f"Redis cache HIT for {func_name}")
                return pickle.loads(cached_result)
            else:
                context.log.info(f"Redis cache MISS for {func_name}")
        except Exception as e:
            context.log.error(
                f"Redis cache read failed for {func_name}: {str(e)}, computing result"
            )

        context.log.debug(f"Computing result for {func_name}")
        result = func(*args, **kwargs)

        try:
            serialized_result = pickle.dumps(result)
            redis_client.setex(cache_key, ttl, serialized_result)
            context.log.debug(
                f"Redis cache WRITE successful for {func_name} (expires in {ttl} seconds)"
            )
        except Exception as e:
            context.log.error(f"Redis cache write failed for {func_name}: {str(e)}")

        return result

    return wrapper
