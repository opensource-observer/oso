from enum import Enum
from time import sleep
from typing import Any, Callable, Dict, Generator, Never, Optional, TypeVar

from dagster import AssetExecutionContext
from gql import Client
from graphql import DocumentNode
from pydantic import BaseModel, Field

from .errors import NullOrUndefinedValueError

T = TypeVar("T")


# An enum for specifying time intervals
class TimeInterval(Enum):
    Hourly = 0
    Daily = 1
    Weekly = 2
    Monthly = 3


# Configures how we should handle incoming data
class SourceMode(Enum):
    # Add new time-partitioned data incrementally
    Incremental = 0
    # Overwrite the entire dataset on each import
    Overwrite = 1


# Simple snake case to camel case
def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def to_lower_camel_case(snake_str):
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    camel_string = to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]


def safeCast[T](x: T) -> T:
    """
    Explicitly mark that a cast is safe.
    e.g. `safeCast(x as string[])`.
    """
    y: T = x
    return y


def assertNever(_x: Never) -> Never:
    """
    Asserts that a branch is never taken.
    Useful for exhaustiveness checking.
    """
    raise Exception("unexpected branch taken")


def ensure[T](x: Optional[T], msg: str) -> T:
    """
    Asserts that a value is not null or undefined.

    Parameters
    ----------
    x: Optional[T]
        The object to ensure
    msg: str
        The message to print if None

    Returns
    -------
    T
        the ensured value
    """
    if x is None:
        raise NullOrUndefinedValueError(
            f"Value must not be undefined or null{f' - {msg}' if msg else ''}"
        )
    else:
        y: T = x
        return y


def generate_steps(total: int, step: int):
    """
    Generates a sequence of numbers from 0 up to the specified total, incrementing by the specified step.
    If the total is not divisible by the step, the last iteration will yield the remaining value.

    Args:
        total (int): The desired total value.
        step (int): The increment value for each iteration.

    Yields:
        int: The next number in the sequence.

    Example:
        >>> for num in generate_steps(10, 3):
        ...     print(num)
        0
        3
        6
        9
        10
    """

    for i in range(0, total, step):
        yield i
    if total % step != 0:
        yield total


class QueryArguments(BaseModel):
    offset: int = Field(
        ...,
        ge=0,
        description="The offset to start fetching nodes from.",
    )


class QueryConfig(BaseModel):
    limit: int = Field(
        ...,
        gt=0,
        description="Maximum number of nodes to fetch per query.",
    )
    minimum_limit: int = Field(
        ...,
        gt=0,
        description="Minimum limit for the query, after which the query will fail.",
    )
    query_arguments: QueryArguments = Field(
        ...,
        description="Arguments for the query to be executed.",
    )
    step_key: str = Field(
        ...,
        description="The key in the query arguments to update with the offset.",
    )
    extract_fn: Callable[[Dict[str, Any]], Any] = Field(
        ...,
        description="Function to extract the data from the query response.",
    )
    ratelimit_wait_seconds: int = Field(
        ...,
        gt=0,
        description="Time to wait before retrying the query after being rate limited.",
    )


class QueryRetriesExceeded(Exception):
    """
    Exception raised when the maximum number of query retries is exceeded.
    """


def query_with_retry(
    client: Client,
    context: AssetExecutionContext,
    query_str: DocumentNode,
    total_count: int,
    config: QueryConfig,
) -> Generator[Dict[str, Any], None, None]:
    """
    Queries the GraphQL API with retry logic. The query will be retried
    with a lower limit if it fails. If the limit reaches the minimum limit,
    the query will fail. It will also handle rate limiting by waiting for
    the specified number of seconds before retrying.

    Args:
        client (Client): The GraphQL client to execute the query.
        context (AssetExecutionContext): The context for the asset.
        query_str (DocumentNode): The GraphQL query to execute.
        total_count (int): The total number of nodes to fetch.
        config (QueryConfig): The configuration for the query.

    Yields:
        Dict[str, Any]: A dictionary containing the transaction nodes.
    """

    max_retries = 3
    current_index = 0
    limit = config.limit
    steps = list(generate_steps(total_count, limit))

    while limit >= config.minimum_limit:
        while current_index < len(steps):
            setattr(config.query_arguments, config.step_key, steps[current_index])

            if max_retries == 0:
                raise ValueError(
                    "Query failed after reaching the maximum number of retries."
                )

            try:
                query = client.execute(
                    query_str, variable_values=config.query_arguments.model_dump()
                )
                context.log.info(
                    f"Fetching transaction {steps[current_index]}/{total_count}"
                )
                current_index += 1
                yield config.extract_fn(query)
            except Exception as exception:
                context.log.error(f"Query failed with error: {exception}")
                if "429" in str(exception):
                    context.log.info(
                        f"Got rate-limited, retrying in {config.ratelimit_wait_seconds} seconds."
                    )
                    sleep(config.ratelimit_wait_seconds)
                    max_retries -= 1
                    continue
                limit //= 2
                steps = list(generate_steps(total_count, limit))
                current_index *= 2
                if limit < config.minimum_limit:
                    raise QueryRetriesExceeded(
                        f"Query failed after reaching the minimum limit of {limit}."
                    ) from exception
                context.log.info(f"Retrying with limit: {limit}")
        break


def stringify_large_integers(data: Any) -> Any:
    """
    Recursively convert integers exceeding 64-bit range to strings.

    Args:
        data: Array of objects, dict, list, or any primitive value

    Returns:
        Modified data with large integers converted to strings
    """
    MAX_64BIT: int = 2**63 - 1
    MIN_64BIT: int = -(2**63)

    def _convert_recursive(obj: Any) -> Any:
        type_handlers = {
            int: lambda x: str(x) if (x > MAX_64BIT or x < MIN_64BIT) else x,
            dict: lambda x: {k: _convert_recursive(v) for k, v in x.items()},
            list: lambda x: [_convert_recursive(item) for item in x],
            tuple: lambda x: tuple(_convert_recursive(item) for item in x),
        }

        handler = type_handlers.get(type(obj), lambda x: x)
        return handler(obj)

    return _convert_recursive(data)


def is_number(s) -> bool:
    """Return True if s can be converted to a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False
