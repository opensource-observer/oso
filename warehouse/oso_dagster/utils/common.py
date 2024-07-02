from enum import Enum

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