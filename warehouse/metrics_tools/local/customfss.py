"""
This is a custom file system for use with pyiceberg. The reason we need this is
only because minio is using a certificate we don't trust. 

The right fix would be to temporarily copy the minio certificatet into the
current session, but this was quick and hacky.
"""

import logging
from functools import partial
from typing import Callable, Dict

from botocore import UNSIGNED
from fsspec import AbstractFileSystem
from pyiceberg.io import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    S3_ACCESS_KEY_ID,
    S3_CONNECT_TIMEOUT,
    S3_ENDPOINT,
    S3_PROXY_URI,
    S3_REGION,
    S3_SECRET_ACCESS_KEY,
    S3_SESSION_TOKEN,
)
from pyiceberg.io.fsspec import SIGNERS
from pyiceberg.typedef import Properties
from pyiceberg.utils.properties import get_first_property_value

logger = logging.getLogger(__name__)


def _s3(properties: Properties) -> AbstractFileSystem:
    from s3fs import S3FileSystem

    logger.info("Using custom S3FileSystem without TLS validation")

    client_kwargs = {
        "endpoint_url": properties.get(S3_ENDPOINT),
        "aws_access_key_id": get_first_property_value(
            properties, S3_ACCESS_KEY_ID, AWS_ACCESS_KEY_ID
        ),
        "aws_secret_access_key": get_first_property_value(
            properties, S3_SECRET_ACCESS_KEY, AWS_SECRET_ACCESS_KEY
        ),
        "aws_session_token": get_first_property_value(
            properties, S3_SESSION_TOKEN, AWS_SESSION_TOKEN
        ),
        "region_name": get_first_property_value(properties, S3_REGION, AWS_REGION),
        "verify": False,
    }
    if properties.get("s3.verify"):
        client_kwargs["verify"] = properties.get("s3.verify")
    config_kwargs = {}
    register_events: Dict[str, Callable[[Properties], None]] = {}

    if signer := properties.get("s3.signer"):
        logger.info("Loading signer %s", signer)
        if signer_func := SIGNERS.get(signer):
            signer_func_with_properties = partial(signer_func, properties)
            register_events["before-sign.s3"] = signer_func_with_properties  # type: ignore

            # Disable the AWS Signer
            config_kwargs["signature_version"] = UNSIGNED
        else:
            raise ValueError(f"Signer not available: {signer}")

    if proxy_uri := properties.get(S3_PROXY_URI):
        config_kwargs["proxies"] = {"http": proxy_uri, "https": proxy_uri}

    if connect_timeout := properties.get(S3_CONNECT_TIMEOUT):
        config_kwargs["connect_timeout"] = float(connect_timeout)

    fs = S3FileSystem(client_kwargs=client_kwargs, config_kwargs=config_kwargs)

    for event_name, event_function in register_events.items():
        fs.s3.meta.events.register_last(event_name, event_function, unique_id=1925)  # type: ignore

    return fs
