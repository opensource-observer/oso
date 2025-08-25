import asyncio
import logging
import time
from pathlib import Path
from typing import Type, cast, Optional, Dict, Any
from urllib.parse import ParseResult, parse_qsl, urlparse

import hishel
import httpx
import requests
from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import (
    RedisError,
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)
from redis.retry import Retry
import ssl

logger = logging.getLogger(__name__)

class RedisConnectionError(Exception):
    """Custom exception for Redis connection failures."""
    pass

class RedisConfigurationError(Exception):
    """Custom exception for Redis configuration issues."""
    pass


def file_factory(t: Type[hishel.FileStorage | hishel.AsyncFileStorage]):
    def _f(parsed_uri: ParseResult) -> hishel.BaseStorage | hishel.AsyncBaseStorage:
        if parsed_uri.netloc != "":
            raise Exception(
                "Failed to configure file cache. format must be file:///some/abs/path (notice three slashes)"
            )
        params = dict(parse_qsl(parsed_uri.query))
        ttl = int(params.get("ttl", 3600))
        logger.debug("Using the file system for the hishel http cache")
        return t(base_path=Path(parsed_uri.path), ttl=ttl)

    return _f


def create_ssl_context(verify_mode: str = "required") -> ssl.SSLContext:
    """Create an SSL context for Redis connection.
    
    Args:
        verify_mode: SSL certificate verification mode ('required', 'optional', 'none')
        
    Returns:
        ssl.SSLContext: Configured SSL context
    """
    verify_modes = {
        "required": ssl.CERT_REQUIRED,
        "optional": ssl.CERT_OPTIONAL,
        "none": ssl.CERT_NONE
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.verify_mode = verify_modes.get(verify_mode, ssl.CERT_REQUIRED)
    return ssl_context

def create_redis_client(
    parsed_uri: ParseResult,
    params: Dict[str, str]
) -> Redis:
    """Create a Redis client with proper configuration and connection pooling.
    
    Args:
        parsed_uri: Parsed Redis URI
        params: Additional parameters from URI query string
        
    Returns:
        Redis: Configured Redis client
        
    Raises:
        RedisConfigurationError: If configuration is invalid
        RedisConnectionError: If connection fails
    """
    if not parsed_uri.hostname:
        raise RedisConfigurationError("Redis hostname is required")
        
    try:
        # Parse connection parameters
        socket_timeout = float(params.get("socket_timeout", "5.0"))
        socket_connect_timeout = float(params.get("connect_timeout", "5.0"))
        max_connections = int(params.get("max_connections", "10"))
        retry_on_timeout = params.get("retry_on_timeout", "true").lower() == "true"
        ssl_verify_mode = params.get("ssl_verify", "required")
        
        # Create connection pool
        pool = ConnectionPool(
            host=parsed_uri.hostname,
            port=parsed_uri.port or 6379,
            username=parsed_uri.username,
            password=parsed_uri.password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            ssl=True,
            ssl_cert_reqs=ssl_verify_mode,
            ssl_context=create_ssl_context(ssl_verify_mode)
        )
        
        client = Redis(
            connection_pool=pool,
            retry=Retry(
                max_attempts=3,
                backoff_factor=1.5
            )
        )
        
    
        client.ping()
        logger.info(
            "Successfully connected to Redis",
            extra={
                "host": parsed_uri.hostname,
                "port": parsed_uri.port or 6379,
                "max_connections": max_connections
            }
        )
        return client
        
    except (ValueError, TypeError) as e:
        raise RedisConfigurationError(f"Invalid Redis configuration: {str(e)}")
    except (RedisConnectionError, RedisTimeoutError) as e:
        raise RedisConnectionError(f"Failed to connect to Redis: {str(e)}")
    except RedisError as e:
        raise RedisConnectionError(f"Redis error: {str(e)}")

def redis_factory(t: Type[hishel.RedisStorage | hishel.AsyncRedisStorage]):
    """Factory function for creating Redis storage instances.
    
    Args:
        t: Redis storage type (sync or async)
        
    Returns:
        Callable: Factory function for creating storage instances
    """
    def _f(parsed_uri: ParseResult) -> hishel.BaseStorage | hishel.AsyncBaseStorage:
        try:
            params = dict(parse_qsl(parsed_uri.query))
            ttl = int(params.get("ttl", "3600"))
            
            client = create_redis_client(parsed_uri, params)
            
            storage = t(client=client, ttl=ttl)
            logger.debug(
                "Created Redis storage",
                extra={
                    "storage_type": t.__name__,
                    "ttl": ttl
                }
            )
            return storage
            
        except (RedisConfigurationError, RedisConnectionError) as e:
            logger.error(
                "Failed to create Redis storage",
                extra={
                    "error": str(e),
                    "storage_type": t.__name__
                }
            )
            raise
    
    return _f


FACTORIES = {
    "sync": {
        "file": file_factory(hishel.FileStorage),
        "redis": redis_factory(hishel.RedisStorage),
    },
    "async": {
        "file": file_factory(hishel.AsyncFileStorage),
        "redis": redis_factory(hishel.AsyncRedisStorage),
    },
}


def get_sync_http_cache_storage(cache_uri: str) -> hishel.BaseStorage | None:
    parsed_uri = urlparse(cache_uri)

    if parsed_uri.scheme not in FACTORIES["sync"]:
        return None

    factory = FACTORIES["sync"][parsed_uri.scheme]
    return cast(hishel.BaseStorage, factory(parsed_uri))


def get_async_http_cache_storage(cache_uri: str) -> hishel.AsyncBaseStorage | None:
    parsed_uri = urlparse(cache_uri)



    factory = FACTORIES["async"][parsed_uri.scheme]
    return cast(hishel.AsyncBaseStorage, factory(parsed_uri))



async def wait_for_ok_async(url: str, timeout: int = 60):
    start = time.time()
    async with httpx.AsyncClient() as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return
            except httpx.RequestError:
                await asyncio.sleep(1)
    raise TimeoutError(f"Failed to connect to {url} after {timeout} seconds")
