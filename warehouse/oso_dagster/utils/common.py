from enum import Enum
from typing import TypeVar, Never, Optional
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
            f"Value must not be undefined or null{f" - {msg}" if msg else ""}"
        )
    else:
        y: T = x
        return y