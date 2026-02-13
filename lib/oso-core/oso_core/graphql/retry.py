import random
import time
import typing as t
from http.client import IncompleteRead, RemoteDisconnected

from gql.transport.exceptions import (
    TransportError,
    TransportQueryError,
    TransportServerError,
)
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

from .types import GraphQLLogger, RetryConfig

D = t.TypeVar("D")


def sanitize_error_message(
    error_message: str, endpoint: str, masked_endpoint: t.Optional[str] = None
) -> str:
    """
    Sanitize error messages by replacing the real endpoint with a masked endpoint.

    Args:
        error_message: The original error message that may contain URLs.
        endpoint: The real endpoint URL to be replaced.
        masked_endpoint: The masked endpoint URL to replace with.

    Returns:
        Sanitized error message with sensitive URLs replaced.
    """
    if not masked_endpoint or not masked_endpoint.strip():
        return error_message

    return error_message.replace(endpoint, masked_endpoint)


def execute_with_retry(
    func: t.Callable[[], D],
    retry_config: t.Optional[RetryConfig],
    logger: GraphQLLogger,
    operation_name: str = "GraphQL operation",
    endpoint: t.Optional[str] = None,
    masked_endpoint: t.Optional[str] = None,
) -> D:
    """
    Execute a function with retry mechanism and exponential backoff.

    Args:
        func: The function to execute.
        retry_config: Retry configuration. If None, no retries are performed.
        logger: Logger instance with debug/info/warning/error methods.
        operation_name: Name of the operation for logging.
        endpoint: The real endpoint URL for sanitization.
        masked_endpoint: The masked endpoint URL for sanitization.

    Returns:
        The result of the function execution.
    """
    if not retry_config:
        return func()

    for attempt in range(retry_config.max_retries + 1):
        try:
            return func()
        except (
            TransportError,
            TransportServerError,
            TransportQueryError,
            ChunkedEncodingError,
            RequestsConnectionError,
            Timeout,
            RemoteDisconnected,
            IncompleteRead,
        ) as e:
            sanitized_error = sanitize_error_message(
                str(e), endpoint or "", masked_endpoint
            )
            if attempt == retry_config.max_retries:
                logger.error(
                    f"{operation_name} failed after {retry_config.max_retries} "
                    f"retries: {sanitized_error}"
                )
                raise

            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier**attempt),
                retry_config.max_delay,
            )

            if retry_config.jitter:
                delay += random.uniform(0, delay * 0.1)

            logger.warning(
                f"{operation_name} failed (attempt {attempt + 1}/"
                f"{retry_config.max_retries + 1}): {sanitized_error}. "
                f"Retrying in {delay:.2f} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError("Retry loop exited without returning or raising")


def execute_with_adaptive_retry(
    func: t.Callable[[t.Optional[int]], D],
    retry_config: t.Optional[RetryConfig],
    logger: GraphQLLogger,
    initial_page_size: t.Optional[int],
    operation_name: str = "GraphQL operation",
    endpoint: t.Optional[str] = None,
    masked_endpoint: t.Optional[str] = None,
) -> t.Optional[D]:
    """
    Execute a function with retry mechanism that reduces page size on failures.

    Args:
        func: Function that accepts optional page_size parameter.
        retry_config: Retry configuration with page size reduction.
        logger: Logger instance with debug/info/warning/error methods.
        initial_page_size: Initial page size to start with.
        operation_name: Name of the operation for logging.
        endpoint: The real endpoint URL for sanitization.
        masked_endpoint: The masked endpoint URL for sanitization.

    Returns:
        The result of the function execution, or None if continue_on_failure is True.
    """
    if not retry_config or not retry_config.reduce_page_size or not initial_page_size:
        return execute_with_retry(
            lambda: func(None),
            retry_config,
            logger,
            operation_name,
            endpoint,
            masked_endpoint,
        )

    current_page_size = initial_page_size

    for attempt in range(retry_config.max_retries + 1):
        try:
            logger.debug(
                f"{operation_name}: Attempting with page_size={current_page_size} "
                f"(attempt {attempt + 1}/{retry_config.max_retries + 1})"
            )
            result = func(current_page_size)

            if attempt > 0:
                logger.info(
                    f"{operation_name}: SUCCESS after {attempt} retries with "
                    f"page_size={current_page_size} - resetting to original "
                    f"size {initial_page_size} for next page"
                )
            else:
                logger.debug(
                    f"{operation_name}: SUCCESS on first attempt with "
                    f"page_size={current_page_size}"
                )

            return result
        except (
            TransportError,
            TransportServerError,
            TransportQueryError,
            ChunkedEncodingError,
            RequestsConnectionError,
            Timeout,
            RemoteDisconnected,
            IncompleteRead,
        ) as e:
            if attempt == retry_config.max_retries:
                if retry_config.continue_on_failure:
                    logger.error(
                        f"{operation_name} failed after {retry_config.max_retries} "
                        f"retries: {sanitize_error_message(str(e), endpoint or '', masked_endpoint)}. "
                        "Continuing due to continue_on_failure=True"
                    )
                    return None

                logger.error(
                    f"{operation_name} failed after {retry_config.max_retries} "
                    f"retries: {sanitize_error_message(str(e), endpoint or '', masked_endpoint)}"
                )
                raise

            old_page_size = current_page_size
            if current_page_size and retry_config.reduce_page_size:
                new_page_size = max(
                    int(current_page_size * retry_config.page_size_reduction_factor),
                    retry_config.min_page_size,
                )
                if new_page_size < current_page_size:
                    current_page_size = new_page_size
                    logger.warning(
                        f"{operation_name}: FAILURE (attempt {attempt + 1}) - "
                        f"reducing page size from {old_page_size} to {current_page_size}"
                    )
                else:
                    logger.warning(
                        f"{operation_name}: FAILURE (attempt {attempt + 1}) - "
                        f"keeping minimum page size {current_page_size}"
                    )
            else:
                logger.warning(
                    f"{operation_name}: FAILURE (attempt {attempt + 1}) - "
                    f"keeping page size {current_page_size} (reduction disabled)"
                )

            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier**attempt),
                retry_config.max_delay,
            )

            if retry_config.jitter:
                delay += random.uniform(0, delay * 0.1)

            logger.warning(
                f"{operation_name}: Retrying in {delay:.2f} seconds... "
                f"Error: {sanitize_error_message(str(e), endpoint or '', masked_endpoint)}"
            )

            start_sleep = time.time()
            time.sleep(delay)
            actual_delay = time.time() - start_sleep

            logger.info(
                f"{operation_name}: Waited {actual_delay:.2f} seconds, "
                f"starting retry attempt {attempt + 2}"
            )

    raise RuntimeError("Retry loop exited without returning or raising")
