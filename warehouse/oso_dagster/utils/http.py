from typing import Type, cast
from urllib.parse import urlparse, ParseResult, parse_qsl
from pathlib import Path
import logging

from redis import Redis
import hishel

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


def redis_factory(t: Type[hishel.RedisStorage | hishel.AsyncRedisStorage]):
    def _f(parsed_uri: ParseResult) -> hishel.BaseStorage | hishel.AsyncBaseStorage:
        assert parsed_uri.hostname is not None

        client = Redis(
            host=parsed_uri.hostname,
            password=parsed_uri.password,
            username=parsed_uri.password,
            port=parsed_uri.port or 6379,
        )
        params = dict(parse_qsl(parsed_uri.query))
        ttl = int(params.get("ttl", 3600))
        return t(client=client, ttl=ttl)

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


def get_sync_http_cache_storage(cache_uri: str) -> hishel.BaseStorage:
    parsed_uri = urlparse(cache_uri)

    factory = FACTORIES["sync"][parsed_uri.scheme]
    return cast(hishel.BaseStorage, factory(parsed_uri))


def get_async_http_cache_storage(cache_uri: str) -> hishel.AsyncBaseStorage:
    parsed_uri = urlparse(cache_uri)

    factory = FACTORIES["sync"][parsed_uri.scheme]
    return cast(hishel.AsyncBaseStorage, factory(parsed_uri))
