import typing as t
from dataclasses import dataclass
from enum import Enum


class GraphQLLogger(t.Protocol):
    """Protocol for logger objects used in GraphQL operations."""

    def debug(self, *args, **kwargs) -> t.Any: ...
    def info(self, *args, **kwargs) -> t.Any: ...
    def warning(self, *args, **kwargs) -> t.Any: ...
    def error(self, *args, **kwargs) -> t.Any: ...


class PaginationType(Enum):
    """Supported pagination types."""

    NONE = "none"
    OFFSET = "offset"
    CURSOR = "cursor"
    RELAY = "relay"
    KEYSET = "keyset"


@dataclass
class PaginationConfig:
    """Configuration for pagination in GraphQL queries."""

    type: PaginationType
    page_size: int = 50
    max_pages: t.Optional[int] = None
    rate_limit_seconds: float = 0.0

    offset_field: str = "offset"
    limit_field: str = "limit"
    total_count_path: t.Optional[str] = None

    cursor_field: str = "after"
    page_size_field: str = "first"
    next_cursor_path: str = "pageInfo.endCursor"
    has_next_path: str = "pageInfo.hasNextPage"

    edge_path: str = "edges"
    node_path: str = "node"

    order_by_field: str = "id"
    last_value_field: str = "id_gt"
    cursor_key: str = "id"
    order_direction: str = "asc"

    stop_condition: t.Optional[t.Callable[[t.Dict[str, t.Any], int], bool]] = None


@dataclass
class RetryConfig:
    """Configuration for retry mechanism with exponential backoff and page size reduction."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    reduce_page_size: bool = True
    min_page_size: int = 10
    page_size_reduction_factor: float = 0.5
    continue_on_failure: bool = False


@dataclass
class GraphQLPaginationState:
    """State information for resuming GraphQL pagination."""

    last_cursor: t.Optional[t.Any] = None
    pagination_type: PaginationType = PaginationType.KEYSET
    checkpoint_field: str = "id"
    total_processed: int = 0
    successful_pages: int = 0
    last_checkpoint_value: t.Optional[t.Any] = None


@dataclass
class PaginationResult:
    """
    Result of paginated query execution.

    Args:
        successful_pages: Number of pages successfully fetched.
        total_items: Total number of items collected.
    """

    successful_pages: int
    total_items: int
