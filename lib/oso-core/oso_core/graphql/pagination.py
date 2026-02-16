import time
import typing as t
from http.client import IncompleteRead, RemoteDisconnected

from gql import Client, gql
from gql.transport.exceptions import TransportError
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

from .retry import execute_with_adaptive_retry, sanitize_error_message
from .types import (
    GraphQLLogger,
    PaginationConfig,
    PaginationResult,
    PaginationType,
    RetryConfig,
)


def get_nested_value(data: t.Dict[str, t.Any], path: str) -> t.Any:
    """Get a value from nested dictionary using dot notation path.

    Args:
        data: The dictionary to extract value from.
        path: Dot-separated path to the value (e.g., "pageInfo.endCursor").

    Returns:
        The value at the specified path, or None if not found.
    """
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value


def extract_data_for_pagination(
    result: t.Dict[str, t.Any],
    target_query: str,
    transform_fn: t.Optional[t.Callable[[t.Any], t.Any]],
    pagination_config: t.Optional[PaginationConfig],
) -> tuple[t.List[t.Any], t.Optional[t.Dict[str, t.Any]]]:
    """Extract data and pagination info from the GraphQL query result.

    Args:
        result: The GraphQL query result.
        target_query: The target query field name.
        transform_fn: Optional transformation function to apply to the result.
        pagination_config: Pagination configuration.

    Returns:
        A tuple of (data_items, pagination_info) where pagination_info contains
        type-specific pagination metadata.
    """
    if transform_fn:
        data = transform_fn(result)
    else:
        data = result.get(target_query, [])

    if not isinstance(data, list):
        if pagination_config and pagination_config.type == PaginationType.RELAY:
            edges = get_nested_value(data, pagination_config.edge_path) or []
            data = [
                get_nested_value(edge, pagination_config.node_path) for edge in edges
            ]
        else:
            data = [data] if data else []

    pagination_info = None
    if pagination_config:
        if pagination_config.type == PaginationType.OFFSET:
            total_count = None
            if pagination_config.total_count_path:
                total_count = get_nested_value(
                    result.get(target_query, {}),
                    pagination_config.total_count_path,
                )
            pagination_info = {"total_count": total_count}

        elif pagination_config.type in (PaginationType.CURSOR, PaginationType.RELAY):
            target_data = result.get(target_query, {})
            next_cursor = get_nested_value(
                target_data, pagination_config.next_cursor_path
            )
            has_next = get_nested_value(target_data, pagination_config.has_next_path)

            pagination_info = {
                "next_cursor": next_cursor,
                "has_next": has_next,
            }

    return data, pagination_info


class PaginationVariableManager:
    """Manages query variables across pagination cycles.

    This class handles the initialization and updating of variables for different
    pagination types (OFFSET, CURSOR, RELAY, KEYSET).
    """

    def __init__(
        self,
        pagination_config: t.Optional[PaginationConfig],
        initial_parameters: t.Optional[t.Dict[str, t.Dict[str, t.Any]]],
    ):
        self.pagination_config = pagination_config
        self.variables = self._initialize_variables(initial_parameters)

    def _initialize_variables(
        self, initial_parameters: t.Optional[t.Dict[str, t.Dict[str, t.Any]]]
    ) -> t.Dict[str, t.Any]:
        """Initialize variables from parameters."""
        return {
            key: param["value"] for key, param in (initial_parameters or {}).items()
        }

    def get_variables_for_page(
        self,
        page_number: int,
        total_items: int,
        page_size: t.Optional[int],
    ) -> t.Dict[str, t.Any]:
        """Get query variables for the current page.

        Args:
            page_number: Current page number (0-indexed).
            total_items: Total items processed so far.
            page_size: Current page size (may be reduced from original).

        Returns:
            Dictionary of query variables for this page.
        """
        query_variables = self.variables.copy()

        if not self.pagination_config or page_size is None:
            return query_variables

        effective_page_size = page_size

        if self.pagination_config.type == PaginationType.OFFSET:
            query_variables[self.pagination_config.offset_field] = total_items
            query_variables[self.pagination_config.limit_field] = effective_page_size

        elif self.pagination_config.type in (
            PaginationType.CURSOR,
            PaginationType.RELAY,
        ):
            if (
                page_number == 0
                and self.pagination_config.cursor_field not in query_variables
            ):
                query_variables[self.pagination_config.cursor_field] = None
            query_variables[self.pagination_config.page_size_field] = (
                effective_page_size
            )

        elif self.pagination_config.type == PaginationType.KEYSET:
            query_variables["orderBy"] = self.pagination_config.order_by_field
            query_variables["orderDirection"] = self.pagination_config.order_direction
            query_variables[self.pagination_config.page_size_field] = (
                effective_page_size
            )
            query_variables.setdefault("where", {})
            if page_number == 0:
                query_variables["where"].setdefault(
                    self.pagination_config.last_value_field, "0"
                )

        return query_variables

    def update_for_next_page(
        self,
        pagination_info: t.Optional[t.Dict[str, t.Any]],
        last_item: t.Optional[t.Dict[str, t.Any]],
    ) -> None:
        """Update internal state for the next page based on pagination type.

        Args:
            pagination_info: Pagination information from the response.
            last_item: Last item from the current page.
        """
        if not self.pagination_config:
            return

        if self.pagination_config.type == PaginationType.OFFSET:
            pass

        elif self.pagination_config.type in (
            PaginationType.CURSOR,
            PaginationType.RELAY,
        ):
            if pagination_info and pagination_info.get("next_cursor"):
                self.variables[self.pagination_config.cursor_field] = pagination_info[
                    "next_cursor"
                ]

        elif self.pagination_config.type == PaginationType.KEYSET:
            if last_item:
                cursor_key = self.pagination_config.cursor_key
                if cursor_key in last_item:
                    last_value = get_nested_value(last_item, cursor_key)
                    self.variables.setdefault("where", {})
                    self.variables["where"][self.pagination_config.last_value_field] = (
                        last_value
                    )


class PaginationDecisionEngine:
    """Determines if more pages should be fetched based on pagination type and configuration.

    This class consolidates the has_more logic for different pagination strategies.
    """

    @staticmethod
    def compute_has_more(
        pagination_config: t.Optional[PaginationConfig],
        pagination_info: t.Optional[t.Dict[str, t.Any]],
        items_in_page: int,
        total_items: int,
        successful_pages: int,
        data_items: t.List[t.Any],
    ) -> bool:
        """Determine if more pages should be fetched.

        Args:
            pagination_config: Pagination configuration.
            pagination_info: Pagination information from the response.
            items_in_page: Number of items in the current page.
            total_items: Total items processed so far.
            successful_pages: Number of successful pages so far.
            data_items: Data items from the current page.

        Returns:
            True if more pages should be fetched, False otherwise.
        """
        if not pagination_config:
            return False

        if pagination_config.type == PaginationType.NONE:
            return False

        if (
            pagination_config.max_pages
            and successful_pages >= pagination_config.max_pages
        ):
            return False

        if pagination_config.type == PaginationType.OFFSET:
            if pagination_info and pagination_info.get("total_count") is not None:
                return total_items < pagination_info["total_count"]
            else:
                return items_in_page > 0

        elif pagination_config.type in (PaginationType.CURSOR, PaginationType.RELAY):
            if pagination_info:
                return bool(
                    pagination_info.get("has_next", False)
                    and pagination_info.get("next_cursor")
                )
            return False

        elif pagination_config.type == PaginationType.KEYSET:
            if items_in_page > 0 and isinstance(data_items, list):
                last_item = data_items[-1]
                cursor_key = pagination_config.cursor_key
                return cursor_key in last_item
            return False

        return False


class GraphQLPaginationExecutor:
    """Orchestrates the entire pagination loop for GraphQL queries.

    This class handles variable management, retry logic, and pagination decisions,
    yielding items as they're fetched from the GraphQL API.
    """

    def __init__(
        self,
        client: Client,
        logger: GraphQLLogger,
        pagination_config: t.Optional[PaginationConfig],
        retry_config: t.Optional[RetryConfig],
        endpoint: str,
        masked_endpoint: t.Optional[str],
    ):
        self.client = client
        self.logger = logger
        self.pagination_config = pagination_config
        self.retry_config = retry_config
        self.endpoint = endpoint
        self.masked_endpoint = masked_endpoint
        self.decision_engine = PaginationDecisionEngine()

    def execute_paginated_query(
        self,
        generated_query: str,
        initial_variables: t.Dict[str, t.Any],
        transform_fn: t.Optional[t.Callable[[t.Any], t.Any]],
        target_query: str,
        initial_page_number: int = 0,
        initial_total_items: int = 0,
        page_callback: t.Optional[
            t.Callable[[t.List[t.Any], t.Optional[t.Dict[str, t.Any]], int, int], None]
        ] = None,
    ) -> t.Generator[t.Any, None, PaginationResult]:
        """Execute a paginated GraphQL query, yielding items as they're fetched.

        Args:
            generated_query: The complete GraphQL query string.
            initial_variables: Initial query variables.
            transform_fn: Optional function to transform results.
            target_query: The target query field name.
            initial_page_number: Starting page number (for resume).
            initial_total_items: Starting total items count (for resume).
            page_callback: Optional callback invoked after each successful page.
                Receives (data_items, pagination_info, successful_pages, total_items).

        Yields:
            Individual items from the paginated results.

        Returns:
            PaginationResult with final statistics.
        """
        initial_parameters = {
            key: {"value": value} for key, value in initial_variables.items()
        }
        variable_manager = PaginationVariableManager(
            self.pagination_config, initial_parameters
        )

        has_more = True
        successful_pages = initial_page_number
        total_items = initial_total_items

        while has_more:
            try:
                original_page_size = (
                    self.pagination_config.page_size if self.pagination_config else None
                )

                self.logger.info(
                    f"GraphQL Pagination: Starting page {successful_pages + 1} with page size {original_page_size}"
                )

                def execute_query_with_page_size(
                    page_size: t.Optional[int] = None,
                ) -> t.Dict[str, t.Any]:
                    """Execute query with given page size."""
                    effective_page_size = page_size or original_page_size
                    query_variables = variable_manager.get_variables_for_page(
                        successful_pages, total_items, effective_page_size
                    )

                    self.logger.debug(
                        f"GraphQL Pagination: Executing with variables: {query_variables}"
                    )

                    return self.client.execute(
                        gql(generated_query),
                        variable_values=query_variables,
                    )

                result = execute_with_adaptive_retry(
                    execute_query_with_page_size,
                    self.retry_config,
                    self.logger,
                    original_page_size if self.pagination_config else None,
                    f"GraphQL query execution (page {successful_pages + 1})",
                    endpoint=self.endpoint,
                    masked_endpoint=self.masked_endpoint,
                )

                if result is None:
                    self.logger.info(
                        f"GraphQL query execution (page {successful_pages + 1}) failed and was skipped"
                    )

                    if self.pagination_config and self.pagination_config.type in (
                        PaginationType.CURSOR,
                        PaginationType.RELAY,
                    ):
                        self.logger.info(
                            "Cannot continue cursor-based pagination after failure. Stopping."
                        )
                        break

                    if (
                        self.pagination_config
                        and self.pagination_config.type == PaginationType.OFFSET
                    ):
                        total_items += self.pagination_config.page_size
                        self.logger.info(
                            f"Advancing offset by {self.pagination_config.page_size} to skip failed page. New offset: {total_items}"
                        )

                    continue

                data_items, pagination_info = extract_data_for_pagination(
                    result, target_query, transform_fn, self.pagination_config
                )

                items_in_page = 0
                if isinstance(data_items, list):
                    items_in_page = len(data_items)
                else:
                    items_in_page = 1 if data_items else 0

                total_items += items_in_page
                successful_pages += 1

                self.logger.info(
                    f"GraphQL Pagination: Successfully completed page {successful_pages} "
                    f"with {items_in_page} items (total: {total_items})"
                )

                if page_callback:
                    page_callback(
                        data_items
                        if isinstance(data_items, list)
                        else [data_items]
                        if data_items
                        else [],
                        pagination_info,
                        successful_pages,
                        total_items,
                    )

                if isinstance(data_items, list):
                    for item in data_items:
                        yield item
                else:
                    if data_items:
                        yield data_items

                last_item = (
                    data_items[-1]
                    if isinstance(data_items, list) and data_items
                    else None
                )
                variable_manager.update_for_next_page(pagination_info, last_item)

                if not self.pagination_config:
                    has_more = False
                elif self.pagination_config.stop_condition:
                    has_more = not self.pagination_config.stop_condition(
                        result, successful_pages
                    )
                    if not has_more:
                        self.logger.info("GraphQL Pagination: Stop condition met")
                else:
                    has_more = self.decision_engine.compute_has_more(
                        self.pagination_config,
                        pagination_info,
                        items_in_page,
                        total_items,
                        successful_pages,
                        data_items if isinstance(data_items, list) else [],
                    )

                if (
                    has_more
                    and self.pagination_config
                    and self.pagination_config.rate_limit_seconds > 0
                ):
                    self.logger.debug(
                        f"GraphQL Pagination: Rate limiting for {self.pagination_config.rate_limit_seconds}s"
                    )
                    time.sleep(self.pagination_config.rate_limit_seconds)

            except (
                TransportError,
                ChunkedEncodingError,
                RequestsConnectionError,
                Timeout,
                RemoteDisconnected,
                IncompleteRead,
            ) as e:
                sanitized_error = sanitize_error_message(
                    str(e), self.endpoint, self.masked_endpoint
                )
                self.logger.error(f"GraphQL query execution failed: {sanitized_error}")
                raise ValueError(
                    f"Failed to execute GraphQL query: {sanitized_error}"
                ) from e

        self.logger.info(
            f"GraphQL Pagination: Completed fetching {total_items} total items "
            f"across {successful_pages} successful pages"
        )

        return PaginationResult(
            successful_pages=successful_pages,
            total_items=total_items,
        )
