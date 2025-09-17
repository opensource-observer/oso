import functools
import json
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    Concatenate,
    Dict,
    Generator,
    List,
    Optional,
    ParamSpec,
    Set,
    Tuple,
    TypeVar,
    cast,
)

import dlt
from dagster import AssetExecutionContext, AssetObservation, MetadataValue
from dlt.extract.resource import DltResource
from google.cloud import storage
from google.cloud.exceptions import NotFound
from gql import Client, gql
from gql.transport.exceptions import (
    TransportError,
    TransportQueryError,
    TransportServerError,
)
from gql.transport.requests import RequestsHTTPTransport
from oso_dagster.config import DagsterConfig
from oso_dagster.utils.redis import redis_cache
from requests.exceptions import ChunkedEncodingError

# The maximum depth of the introspection query.
FRAGMENT_MAX_DEPTH = 10

# The introspection query to fetch the schema of a GraphQL resource.
INTROSPECTION_QUERY = """
  query IntrospectionQuery {
    __schema {
      queryType { name }
      mutationType { name }
      subscriptionType { name }
      types {
        ...FullType
      }
      directives {
        name
        description
        locations
        args {
          ...InputValue
        }
      }
    }
  }
  fragment FullType on __Type {
    kind
    name
    description
    fields(includeDeprecated: true) {
      name
      description
      args {
        ...InputValue
      }
      type {
        ...TypeRef
      }
      isDeprecated
      deprecationReason
    }
    inputFields {
      ...InputValue
    }
    interfaces {
      ...TypeRef
    }
    enumValues(includeDeprecated: true) {
      name
      description
      isDeprecated
      deprecationReason
    }
    possibleTypes {
      ...TypeRef
    }
  }
  fragment InputValue on __InputValue {
    name
    description
    type { ...TypeRef }
    defaultValue
  }
  fragment TypeRef on __Type {
    {{ DEPTH }}
  }
"""


def sanitize_error_message(
    error_message: str, endpoint: str, masked_endpoint: Optional[str] = None
) -> str:
    """
    Sanitize error messages by replacing the real endpoint with a masked endpoint to avoid exposing sensitive URLs.

    Args:
        error_message: The original error message that may contain URLs.
        endpoint: The real endpoint URL to be replaced.
        masked_endpoint: The masked endpoint URL to replace with. If None, no sanitization is performed.

    Returns:
        Sanitized error message with sensitive URLs replaced.
    """
    if not masked_endpoint or not masked_endpoint.strip():
        return error_message

    return error_message.replace(endpoint, masked_endpoint)


class PaginationType(Enum):
    """Supported pagination types."""

    OFFSET = "offset"
    CURSOR = "cursor"
    RELAY = "relay"
    KEYSET = "keyset"


@dataclass
class PaginationConfig:
    """
    Configuration for pagination in GraphQL queries.

    Args:
        type: The type of pagination (offset, cursor, or relay).
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        rate_limit_seconds: Seconds to wait between page requests.

        For offset-based pagination:
        offset_field: Name of the offset field (default: "offset").
        limit_field: Name of the limit field (default: "limit").
        total_count_path: (Optional) Path to total count field (e.g., "totalCount").
            If not provided, the pagination will continue until the API returns no more data.

        For cursor-based pagination:
        cursor_field: Name of the cursor field (default: "after").
        page_size_field: Name of the page size field (default: "first").
        next_cursor_path: Path to next cursor value (e.g., "pageInfo.endCursor").
        has_next_path: Path to hasNext field (e.g., "pageInfo.hasNextPage").

        For relay-style pagination:
        Uses cursor-based fields but expects standard Relay connection structure.
        edge_path: Path to edges array (default: "edges").
        node_path: Path to node within edge (default: "node").

        For keyset-style pagination:
        order_by_field: Name of the orderBy field (default: "id").
        order_direction: Order direction, either "asc" or "desc" (default: "asc").
        last_value_field: Name of the field to filter by for the next page (e.g., "id_gt").
        cursor_key: The key in the result item to use as the cursor value (e.g., "id").
        page_size_field: Name of the page size field (default: "first").
    """

    type: PaginationType
    page_size: int = 50
    max_pages: Optional[int] = None
    rate_limit_seconds: float = 0.0

    offset_field: str = "offset"
    limit_field: str = "limit"
    total_count_path: Optional[str] = None

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

    stop_condition: Optional[Callable[[Dict[str, Any], int], bool]] = None


type GraphQLDependencyCallable = Callable[
    [AssetExecutionContext, DagsterConfig, Any], Generator[DltResource, Any, Any]
]


@dataclass
class RetryConfig:
    """
    Configuration for retry mechanism with exponential backoff and page size reduction.

    Args:
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds before first retry (default: 1.0).
        max_delay: Maximum delay in seconds between retries (default: 60.0).
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0).
        jitter: Whether to add random jitter to delays (default: True).
        reduce_page_size: Whether to reduce page size on failures (default: True).
        min_page_size: Minimum page size when reducing (default: 10).
        page_size_reduction_factor: Factor to reduce page size by (default: 0.5).
        continue_on_failure: Whether to log failures and continue instead of raising (default: False).
    """

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
class GraphQLResourceConfig:
    """
    Configuration for a GraphQL resource.

    Args:
        name: The name of the GraphQL resource.
        endpoint: The endpoint of the GraphQL resource.
        masked_endpoint: The masked endpoint of the GraphQL resource.
            If exists, it will be used for logging instead of the real endpoint.
        target_type: The type to target in the introspection query.
        target_query: The query to target in the main query.
        max_depth: The maximum depth of the GraphQL query.
        headers: The headers to include in the introspection query.
        transform_fn: The function to transform the result of the query.
        parameters: The parameters to include in the introspection query.
        pagination: The pagination configuration.
        exclude: Fields to exclude from the GraphQL schema expansion.
        deps_rate_limit_seconds: Seconds to wait between dependency calls.
        deps: Dependencies for the GraphQL resource. If provided, the main query results
              will be used as intermediate data to feed the dependencies, and those
              intermediate rows will be skipped from the final output. The factory can
              only return one consistent data shape, so deps serve as a means to transform
              the intermediate data into the final desired output format.
        retry: Retry configuration for failed queries.
        enable_chunked_resume: Whether to enable chunked resumability for long-running processes.
            When enabled, each successful page is stored as a chunk in GCS, allowing the process
            to resume from where it left off after pre-emption without data loss.
        chunk_gcs_prefix: GCS prefix for storing chunked data and pagination state.
        checkpoint_field: Field name to use for tracking pagination progress
            This field's value from the last processed item will be used to resume pagination.
    """

    name: str
    endpoint: str
    target_type: str
    target_query: str
    max_depth: int = 5
    masked_endpoint: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    transform_fn: Optional[Callable[[Any], Any]] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    pagination: Optional[PaginationConfig] = None
    exclude: Optional[List[str]] = None
    deps_rate_limit_seconds: float = 0.0
    deps: Optional[List[GraphQLDependencyCallable]] = None
    retry: Optional[RetryConfig] = None
    enable_chunked_resume: bool = False
    chunk_gcs_prefix: str = "dlt_chunked_state"
    checkpoint_field: str = "id"


@dataclass
class GraphQLPaginationState:
    """
    State information for resuming GraphQL pagination.

    Args:
        last_cursor: Last cursor/offset value used for pagination.
        pagination_type: Type of pagination being used.
        checkpoint_field: Field name being tracked for checkpointing.
        total_processed: Total number of items processed so far.
        successful_pages: Number of pages successfully completed.
        last_checkpoint_value: Last value of the checkpoint field from processed data.
    """

    last_cursor: Optional[Any] = None
    pagination_type: PaginationType = PaginationType.KEYSET
    checkpoint_field: str = "id"
    total_processed: int = 0
    successful_pages: int = 0
    last_checkpoint_value: Optional[Any] = None


@dataclass
class GraphQLChunkedManifest:
    """
    Manifest tracking the state of a chunked GraphQL resource.

    Args:
        updated_at: ISO timestamp of last update.
        created_at: ISO timestamp of creation.
        pagination_state: Current pagination state for resuming.
        completed_chunks: List of chunk file names that have been stored in GCS.
    """

    updated_at: str
    created_at: str
    pagination_state: GraphQLPaginationState
    completed_chunks: List[str]


def save_page_chunk(
    bucket: storage.Bucket,
    gcs_prefix: str,
    resource_name: str,
    page_data: List[Any],
    page_num: int,
    context: AssetExecutionContext,
) -> str:
    """
    Save a page's data as a chunk in GCS.

    Args:
        bucket: GCS bucket to store the chunk in.
        gcs_prefix: GCS prefix for chunked data.
        resource_name: Name of the GraphQL resource.
        page_data: Data from the successful page to store.
        page_num: Page number for logging purposes.
        context: Execution context for logging.

    Returns:
        The name of the stored chunk file.
    """
    chunk_uuid = str(uuid.uuid4())
    chunk_name = f"chunk.{chunk_uuid}.json"
    chunk_blob = bucket.blob(f"{gcs_prefix}/{resource_name}/{chunk_name}")

    serialized_data = json.dumps(page_data, default=str)
    chunk_blob.upload_from_string(serialized_data)

    context.log.info(
        f"GraphQLChunkedResource: Saved page {page_num} with {len(page_data)} items to {chunk_blob.name}"
    )

    return chunk_name


def load_existing_chunks(
    bucket: storage.Bucket,
    gcs_prefix: str,
    resource_name: str,
    completed_chunks: List[str],
    context: AssetExecutionContext,
) -> Generator[Any, None, None]:
    """
    Load all existing chunks from GCS and yield their data.

    Note: Missing chunks are assumed to have been successfully processed
    in a previous run and cleaned up by the cleanup job. This prevents
    reprocessing data when resuming after cleanup.

    Args:
        bucket: GCS bucket to load chunks from.
        gcs_prefix: GCS prefix for chunked data.
        resource_name: Name of the GraphQL resource.
        completed_chunks: List of chunk file names to load.
        context: Execution context for logging.

    Yields:
        Individual items from the stored chunks.
    """
    chunks_found = 0
    chunks_assumed_processed = 0

    context.log.info(
        f"GraphQLChunkedResource: Loading {len(completed_chunks)} existing chunks"
    )

    for chunk_name in completed_chunks:
        chunk_blob = bucket.blob(f"{gcs_prefix}/{resource_name}/{chunk_name}")
        try:
            if chunk_blob.exists():
                context.log.info(f"GraphQLChunkedResource: Loading chunk {chunk_name}")
                chunk_data = json.loads(chunk_blob.download_as_string())
                chunks_found += 1
                yield from chunk_data
            else:
                context.log.info(
                    f"GraphQLChunkedResource: Chunk {chunk_name} not found, assuming already processed and cleaned up"
                )
                chunks_assumed_processed += 1
        except Exception as e:
            context.log.error(
                f"GraphQLChunkedResource: Failed to load chunk {chunk_name}: {e}"
            )

    context.log.info(
        f"GraphQLChunkedResource: Resume summary, {chunks_found} chunks loaded, "
        f"{chunks_assumed_processed} chunks assumed already processed"
    )


def update_pagination_manifest(
    bucket: storage.Bucket,
    gcs_prefix: str,
    resource_name: str,
    pagination_state: GraphQLPaginationState,
    new_chunk_name: str,
    existing_manifest: Optional[GraphQLChunkedManifest],
    context: AssetExecutionContext,
) -> None:
    """
    Update the pagination manifest with new state and chunk information.

    Args:
        bucket: GCS bucket to store the manifest in.
        gcs_prefix: GCS prefix for chunked data.
        resource_name: Name of the GraphQL resource.
        pagination_state: Current pagination state.
        new_chunk_name: Name of the newly created chunk.
        existing_manifest: Existing manifest to update, or None for new manifest.
        context: Execution context for logging.
    """
    manifest_blob = bucket.blob(f"{gcs_prefix}/{resource_name}/state.json")

    now = datetime.now().isoformat()

    if existing_manifest:
        completed_chunks = existing_manifest.completed_chunks + [new_chunk_name]
        created_at = existing_manifest.created_at
    else:
        completed_chunks = [new_chunk_name]
        created_at = now

    manifest = GraphQLChunkedManifest(
        updated_at=now,
        created_at=created_at,
        pagination_state=pagination_state,
        completed_chunks=completed_chunks,
    )

    manifest_dict = {
        "updated_at": manifest.updated_at,
        "created_at": manifest.created_at,
        "pagination_state": {
            "last_cursor": manifest.pagination_state.last_cursor,
            "pagination_type": manifest.pagination_state.pagination_type.value,
            "checkpoint_field": manifest.pagination_state.checkpoint_field,
            "total_processed": manifest.pagination_state.total_processed,
            "successful_pages": manifest.pagination_state.successful_pages,
            "last_checkpoint_value": manifest.pagination_state.last_checkpoint_value,
        },
        "completed_chunks": manifest.completed_chunks,
        "pending_data": True,
    }

    manifest_blob.upload_from_string(json.dumps(manifest_dict, default=str))

    context.log.info(
        f"GraphQLChunkedResource: Updated manifest with {len(completed_chunks)} chunks, "
        f"last checkpoint: {pagination_state.last_checkpoint_value}"
    )


def load_pagination_manifest(
    bucket: storage.Bucket,
    gcs_prefix: str,
    resource_name: str,
    context: AssetExecutionContext,
) -> Optional[GraphQLChunkedManifest]:
    """
    Load the pagination manifest from GCS.

    Args:
        bucket: GCS bucket to load the manifest from.
        gcs_prefix: GCS prefix for chunked data.
        resource_name: Name of the GraphQL resource.
        context: Execution context for logging.

    Returns:
        The loaded manifest, or None if it doesn't exist or is invalid.
    """
    manifest_blob = bucket.blob(f"{gcs_prefix}/{resource_name}/state.json")

    try:
        if not manifest_blob.exists():
            context.log.info("GraphQLChunkedResource: No existing manifest found")
            return None

        manifest_data = json.loads(manifest_blob.download_as_string())
        context.log.info("GraphQLChunkedResource: Found existing manifest")

        pagination_state = GraphQLPaginationState(
            last_cursor=manifest_data["pagination_state"]["last_cursor"],
            pagination_type=PaginationType(
                manifest_data["pagination_state"]["pagination_type"]
            ),
            checkpoint_field=manifest_data["pagination_state"]["checkpoint_field"],
            total_processed=manifest_data["pagination_state"]["total_processed"],
            successful_pages=manifest_data["pagination_state"]["successful_pages"],
            last_checkpoint_value=manifest_data["pagination_state"][
                "last_checkpoint_value"
            ],
        )

        manifest = GraphQLChunkedManifest(
            updated_at=manifest_data["updated_at"],
            created_at=manifest_data["created_at"],
            pagination_state=pagination_state,
            completed_chunks=manifest_data["completed_chunks"],
        )

        return manifest

    except (NotFound, json.JSONDecodeError, KeyError) as e:
        context.log.warning(
            f"GraphQLChunkedResource: Failed to load manifest: {e}, starting fresh"
        )
        return None


@dataclass
class ChunkedStateLoadResult:
    """
    Result of loading chunked state and data.

    Args:
        data_generator: Generator yielding existing chunk data.
        successful_pages: Number of pages already processed.
        total_items: Total items already processed.
        variables_updates: Updates to apply to query variables for resuming pagination.
        bucket: GCS bucket for saving new chunks (None if chunking disabled/failed).
        manifest: Current manifest state (None if starting fresh).
    """

    data_generator: Generator[Any, None, None]
    successful_pages: int
    total_items: int
    variables_updates: Dict[str, Any]
    bucket: Optional[storage.Bucket]
    manifest: Optional[GraphQLChunkedManifest]


def load_chunked_state_and_data(
    config: GraphQLResourceConfig,
    global_config: DagsterConfig,
    context: AssetExecutionContext,
) -> ChunkedStateLoadResult:
    """
    Load existing chunked state and data for resuming a GraphQL resource.

    Args:
        config: GraphQL resource configuration.
        global_config: Global Dagster configuration.
        context: Execution context for logging.

    Returns:
        ChunkedStateLoadResult with loaded data and state information.
    """
    empty_generator = (item for item in [])

    if not config.enable_chunked_resume:
        return ChunkedStateLoadResult(
            data_generator=empty_generator,
            successful_pages=0,
            total_items=0,
            variables_updates={},
            bucket=None,
            manifest=None,
        )

    try:
        bucket = storage.Client().get_bucket(global_config.gcs_bucket)
        existing_manifest = load_pagination_manifest(
            bucket, config.chunk_gcs_prefix, config.name, context
        )

        if not existing_manifest:
            context.log.info(
                "GraphQLChunkedResource: No existing manifest found, starting fresh"
            )
            return ChunkedStateLoadResult(
                data_generator=empty_generator,
                successful_pages=0,
                total_items=0,
                variables_updates={},
                bucket=bucket,
                manifest=None,
            )

        context.log.info(
            f"GraphQLChunkedResource: Found existing manifest with {len(existing_manifest.completed_chunks)} chunks, "
            f"resuming from checkpoint: {existing_manifest.pagination_state.last_checkpoint_value}"
        )

        data_generator = load_existing_chunks(
            bucket,
            config.chunk_gcs_prefix,
            config.name,
            existing_manifest.completed_chunks,
            context,
        )

        successful_pages = existing_manifest.pagination_state.successful_pages
        total_items = existing_manifest.pagination_state.total_processed

        variables_updates = {}
        if (
            config.pagination
            and existing_manifest.pagination_state.last_cursor is not None
        ):
            if config.pagination.type == PaginationType.OFFSET:
                pass
            elif config.pagination.type in (
                PaginationType.CURSOR,
                PaginationType.RELAY,
            ):
                variables_updates[config.pagination.cursor_field] = (
                    existing_manifest.pagination_state.last_cursor
                )
            elif config.pagination.type == PaginationType.KEYSET:
                if existing_manifest.pagination_state.last_checkpoint_value is not None:
                    variables_updates.setdefault("where", {})
                    variables_updates["where"][config.pagination.last_value_field] = (
                        existing_manifest.pagination_state.last_checkpoint_value
                    )

        return ChunkedStateLoadResult(
            data_generator=data_generator,
            successful_pages=successful_pages,
            total_items=total_items,
            variables_updates=variables_updates,
            bucket=bucket,
            manifest=existing_manifest,
        )

    except Exception as e:
        context.log.error(
            f"GraphQLChunkedResource: Failed to initialize chunked resume: {e}, continuing without chunking"
        )
        return ChunkedStateLoadResult(
            data_generator=empty_generator,
            successful_pages=0,
            total_items=0,
            variables_updates={},
            bucket=None,
            manifest=None,
        )


def save_chunked_state_and_data(
    config: GraphQLResourceConfig,
    context: AssetExecutionContext,
    data_items: List[Any],
    pagination_info: Optional[Dict[str, Any]],
    successful_pages: int,
    total_items: int,
    bucket: storage.Bucket,
    existing_manifest: Optional[GraphQLChunkedManifest],
) -> Optional[GraphQLChunkedManifest]:
    """
    Save the current page's data as a chunk and update the pagination manifest.

    Args:
        config: GraphQL resource configuration.
        context: Execution context for logging.
        data_items: Data items from the current page to save.
        pagination_info: Pagination information from the current page response.
        successful_pages: Current number of successful pages.
        total_items: Current total number of items processed.
        bucket: GCS bucket for storing chunks.
        existing_manifest: Current manifest to update, or None for new manifest.

    Returns:
        Updated manifest, or None if saving failed.
    """
    try:
        checkpoint_value = None
        last_cursor = None

        if isinstance(data_items, list) and len(data_items) > 0:
            last_item = data_items[-1]
            if config.checkpoint_field in last_item:
                checkpoint_value = last_item[config.checkpoint_field]

            if config.pagination:
                if config.pagination.type == PaginationType.OFFSET:
                    last_cursor = total_items
                elif config.pagination.type in (
                    PaginationType.CURSOR,
                    PaginationType.RELAY,
                ):
                    if pagination_info:
                        last_cursor = pagination_info.get("next_cursor")
                elif config.pagination.type == PaginationType.KEYSET:
                    last_cursor = checkpoint_value

        chunk_name = save_page_chunk(
            bucket,
            config.chunk_gcs_prefix,
            config.name,
            data_items if isinstance(data_items, list) else [data_items],
            successful_pages,
            context,
        )

        pagination_state = GraphQLPaginationState(
            last_cursor=last_cursor,
            pagination_type=(
                config.pagination.type if config.pagination else PaginationType.KEYSET
            ),
            checkpoint_field=config.checkpoint_field,
            total_processed=total_items,
            successful_pages=successful_pages,
            last_checkpoint_value=checkpoint_value,
        )

        update_pagination_manifest(
            bucket,
            config.chunk_gcs_prefix,
            config.name,
            pagination_state,
            chunk_name,
            existing_manifest,
            context,
        )

        if existing_manifest:
            existing_manifest.completed_chunks.append(chunk_name)
            existing_manifest.pagination_state = pagination_state
            existing_manifest.updated_at = datetime.now().isoformat()
            return existing_manifest
        else:
            return GraphQLChunkedManifest(
                updated_at=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                pagination_state=pagination_state,
                completed_chunks=[chunk_name],
            )

    except Exception as e:
        context.log.error(
            f"GraphQLChunkedResource: Failed to save chunk for page {successful_pages}: {e}"
        )
        return existing_manifest


def create_fragment(depth: int, max_depth=FRAGMENT_MAX_DEPTH) -> str:
    """
    Create a fragment for the GraphQL introspection query
    that recurses to a given depth.

    Args:
        depth: The depth of the fragment.
        max_depth: The maximum depth of the fragment, defaults to `FRAGMENT_MAX_DEPTH`.

    Returns:
        A string with the GraphQL fragment at the specified depth.
    """

    if depth <= 0 or depth > max_depth:
        return ""

    if depth == 1:
        return "kind name"

    return f"kind name ofType {{ {create_fragment(depth - 1)} }}"


def _get_graphql_introspection(
    endpoint: str,
    headers_tuple: Optional[Tuple[Tuple[str, str], ...]],
    max_depth: int,
) -> Dict[str, Any]:
    """
    Fetch the GraphQL introspection query from the given endpoint.

    Args:
        endpoint: The GraphQL endpoint URL.
        headers_tuple: Headers as a tuple of tuples for hashability.
        max_depth: Maximum depth for the introspection query.

    Returns:
        The introspection query result.
    """
    headers_dict = dict(headers_tuple) if headers_tuple else None

    transport = RequestsHTTPTransport(
        url=endpoint,
        use_json=True,
        headers=headers_dict,
        timeout=300,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )

    populated_query = INTROSPECTION_QUERY.replace(
        "{{ DEPTH }}", create_fragment(max_depth + 5)
    )

    try:
        return client.execute(gql(populated_query))
    except TransportError as exception:
        raise ValueError(
            f"Failed to fetch GraphQL introspection query from {endpoint}.",
        ) from exception


@dataclass(frozen=True)
class _TypeToPython:
    String = "str"
    Int = "int"
    Float = "float"
    Boolean = "bool"
    Date = "date"
    DateTime = "datetime"
    ID = "str"


class TypeToPython:
    """
    A mapping of GraphQL types to Python types.

    Args:
        available_types: The available types in the introspection query.
    """

    def __init__(self, available_types: List[Dict[str, Any]]):
        self.available_types = available_types
        self._scalar_types = {
            attr: getattr(_TypeToPython, attr)
            for attr in dir(_TypeToPython)
            if not attr.startswith("_")
        }

    def __getitem__(self, name: str) -> str:
        """
        Get the Python type for the given GraphQL type.

        Args:
            name: The name of the GraphQL type.

        Returns:
            The Python type for the given GraphQL type.
        """
        if name in self._scalar_types:
            return self._scalar_types[name]

        is_object = next(
            (type_obj for type_obj in self.available_types if type_obj["name"] == name),
            None,
        )

        return f'"{name}"' if is_object else "Any"


def get_type_info(graphql_type: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract core type information from a GraphQL type, handling NULL and LIST wrappers.

    Args:
        graphql_type: The GraphQL type object.

    Returns:
        A dictionary with the core type information.
    """
    if not graphql_type:
        return {
            "kind": "UNKNOWN",
            "name": None,
            "needs_expansion": False,
        }

    if graphql_type["kind"] in ("NON_NULL", "LIST"):
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return {
                "kind": graphql_type["kind"],
                "name": None,
                "is_scalar": False,
            }

        inner_type = get_type_info(graphql_type["ofType"])
        return {
            "kind": graphql_type["kind"],
            "wrapped_kind": inner_type["kind"],
            "name": inner_type["name"],
            "is_scalar": inner_type.get("is_scalar", False),
            "needs_expansion": graphql_type["kind"] == "LIST"
            or inner_type.get("needs_expansion", False),
        }

    if graphql_type["kind"] == "OBJECT":
        return {
            "kind": graphql_type["kind"],
            "name": graphql_type["name"],
            "is_scalar": False,
            "needs_expansion": True,
        }

    is_scalar = graphql_type["kind"] in ("SCALAR", "ENUM")
    return {
        "kind": graphql_type["kind"],
        "name": graphql_type["name"],
        "is_scalar": is_scalar,
        "needs_expansion": not is_scalar,
    }


def resolve_type(graphql_type: Dict[str, Any], type_mapper: TypeToPython) -> str:
    """
    Resolve the type of a GraphQL field to a Python type annotation.

    Args:
        graphql_type: The GraphQL type.
        type_mapper: The instance of the TypeToPython class.

    Returns:
        The Python type annotation for the given GraphQL type.
    """
    if not graphql_type:
        return "Any"

    if graphql_type["kind"] == "NON_NULL":
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return "Any"
        return resolve_type(graphql_type["ofType"], type_mapper)

    if graphql_type["kind"] == "LIST":
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return "List[Any]"
        inner_type = resolve_type(graphql_type["ofType"], type_mapper)
        return f"List[{inner_type}]"

    if graphql_type["kind"] == "ENUM":
        return "str"

    type_name = graphql_type.get("name")
    if not type_name:
        return "Any"

    return type_mapper[type_name]


class FieldExpander:
    """
    Helper class to expand GraphQL fields with proper handling of depth and cycles.
    """

    def __init__(
        self,
        context: AssetExecutionContext,
        types_dict: Dict[str, Dict[str, Any]],
        max_depth: int,
        pagination_config: Optional[PaginationConfig] = None,
        exclude_fields: Optional[List[str]] = None,
    ):
        self.context = context
        self.types_dict = types_dict
        self.max_depth = max_depth
        self.visited_paths: Set[str] = set()
        self.pagination_config = pagination_config
        self.exclude_fields = exclude_fields or []

    def should_expand_pagination_field(self, field_path: str) -> bool:
        """Check if a field is needed for pagination."""
        if not self.pagination_config:
            return False

        pagination_fields = []

        if self.pagination_config.type == PaginationType.OFFSET:
            if self.pagination_config.total_count_path:
                pagination_fields.append(self.pagination_config.total_count_path)

        elif self.pagination_config.type in (
            PaginationType.CURSOR,
            PaginationType.RELAY,
        ):
            pagination_fields.extend(
                [
                    self.pagination_config.next_cursor_path,
                    self.pagination_config.has_next_path,
                ]
            )

        for pagination_field in pagination_fields:
            parts = pagination_field.split(".")
            if field_path.endswith(parts[0]):
                return True

        return False

    def expand_field(
        self,
        field: Dict[str, Any],
        current_path: str = "",
        depth: int = 0,
        field_path: str = "",
    ) -> Optional[str]:
        """
        Expand a field in the introspection query, handling cycles and max depth.
        Returns None if the field should be skipped due to expansion limitations.

        Args:
            field: The field to expand.
            current_path: The current path in the query (for cycle detection).
            depth: Current depth in the query.
            field_path: The dot-separated path of field names for exclusion checking.

        Returns:
            The expanded field as a GraphQL query string, or None if field should be skipped.
        """
        field_name = field.get("name", "")
        if not field_name:
            return None

        full_field_path = f"{field_path}.{field_name}" if field_path else field_name

        for exclude_pattern in self.exclude_fields:
            if full_field_path == exclude_pattern or full_field_path.startswith(
                exclude_pattern + "."
            ):
                return None

        for arg in field.get("args", []):
            if arg.get("type", {}).get("kind") == "NON_NULL":
                self.context.log.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' in '{current_path}' "
                    f"because it has a required argument '{arg['name']}' that cannot be provided."
                )
                return None

        field_type_obj = field.get("type", {})
        if not field_type_obj:
            return field_name

        type_info = get_type_info(field_type_obj)
        field_type_name = type_info.get("name")

        needs_expansion = type_info.get("needs_expansion", False)

        if type_info.get("is_scalar", True) or not field_type_name:
            return field_name

        type_def = self.types_dict.get(field_type_name)
        if not type_def:
            return field_name

        type_fields = type_def.get("fields", [])
        if not type_fields:
            return field_name

        new_path = f"{current_path}.{field_name}.{field_type_name}"
        if new_path in self.visited_paths:
            return field_name

        self.visited_paths.add(new_path)

        is_pagination_field = self.should_expand_pagination_field(field_name)

        if depth >= self.max_depth and not is_pagination_field:
            if needs_expansion:
                self.context.log.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' in '{current_path}' "
                    f"because it requires subfields but reached max depth ({self.max_depth})."
                )
                return None
            return field_name

        expanded_fields = []
        for subfield in type_fields:
            expanded = self.expand_field(subfield, new_path, depth + 1, full_field_path)
            if expanded:
                expanded_fields.append(expanded)

        if not expanded_fields and needs_expansion:
            self.context.log.warning(
                f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' in '{current_path}' "
                f"because none of its subfields could be expanded."
            )
            return None

        if expanded_fields:
            return f"{field_name} {{ {' '.join(expanded_fields)} }}"

        return field_name


def get_query_parameters(
    parameters: Optional[Dict[str, Dict[str, Any]]],
    pagination_config: Optional[PaginationConfig] = None,
) -> tuple[str, str]:
    """
    Get the parameters for the GraphQL query.

    Args:
        parameters: The parameters for the query.
        pagination_config: The pagination configuration.

    Returns:
        A tuple with the parameter definitions and variable references.
    """
    all_params = {}

    if parameters:
        all_params.update(parameters)

    if pagination_config:
        if pagination_config.type == PaginationType.OFFSET:
            all_params[pagination_config.offset_field] = {
                "type": "Int",
                "value": 0,
            }
            all_params[pagination_config.limit_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
        elif pagination_config.type in (PaginationType.CURSOR, PaginationType.RELAY):
            all_params[pagination_config.cursor_field] = {
                "type": "String",
                "value": None,
            }
            all_params[pagination_config.page_size_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
        elif pagination_config.type == PaginationType.KEYSET:
            all_params["orderBy"] = {
                "type": "String!",
                "value": None,
            }
            all_params["orderDirection"] = {
                "type": "String!",
                "value": pagination_config.order_direction,
            }
            all_params[pagination_config.page_size_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
            all_params["where"] = {
                "type": "Domain_filter",
                "value": {pagination_config.order_by_field: 0},
            }

    if not all_params:
        return "", ""

    param_defs = ", ".join(
        [f"${key}: {value['type']}" for key, value in all_params.items()]
    )
    param_refs = ", ".join([f"{key}: ${key}" for key in all_params])

    return f"({param_defs})", f"({param_refs})"


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get a value from nested dictionary using dot notation path."""
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value


D = TypeVar("D")


def log_failure_and_continue(
    context: AssetExecutionContext,
    operation_name: str,
    exception: Exception,
    max_retries: int,
    pagination_metadata: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None,
    masked_endpoint: Optional[str] = None,
) -> None:
    """
    Log a failure with detailed information and continue execution.

    Args:
        context: Execution context for logging.
        operation_name: Name of the operation that failed.
        exception: The exception that caused the failure.
        max_retries: Maximum number of retries that were attempted.
        pagination_metadata: Optional metadata related to pagination at the time of failure.
        endpoint: The real endpoint URL for sanitization.
        masked_endpoint: The masked endpoint URL for sanitization.
    """
    sanitized_error = sanitize_error_message(
        str(exception), endpoint or "", masked_endpoint
    )
    context.log.error(
        f"{operation_name} failed after {max_retries} retries: {sanitized_error}. "
        "Continuing due to continue_on_failure=True"
    )

    exception_chain = []
    current_exception = exception
    while current_exception is not None:
        exception_chain.append(str(current_exception))
        current_exception = current_exception.__cause__ or current_exception.__context__

    failure_reason = "\n".join(exception_chain)

    metadata = {
        "failure_reason": MetadataValue.text(failure_reason),
        "failure_timestamp": MetadataValue.timestamp(datetime.now(timezone.utc)),
        "run_id": MetadataValue.text(context.run_id),
        "status": MetadataValue.text("faulty_range"),
        "operation": MetadataValue.text(operation_name),
        "max_retries": MetadataValue.int(max_retries),
    }

    if pagination_metadata:
        type_map = {
            dict: MetadataValue.json,
            int: MetadataValue.int,
            float: MetadataValue.float,
            bool: lambda x: MetadataValue.text(str(x)),
        }

        for key, value in pagination_metadata.items():
            if value is not None:
                handler = type_map.get(
                    type(value), lambda x: MetadataValue.text(str(x))
                )
                metadata[key] = handler(value)

    context.log_event(
        AssetObservation(
            asset_key=context.asset_key,
            metadata=metadata,
        )
    )


def execute_with_retry(
    func: Callable[[], D],
    retry_config: Optional[RetryConfig],
    context: AssetExecutionContext,
    operation_name: str = "GraphQL operation",
    endpoint: Optional[str] = None,
    masked_endpoint: Optional[str] = None,
) -> D:
    """
    Execute a function with retry mechanism and exponential backoff.

    Args:
        func: The function to execute.
        retry_config: Retry configuration. If None, no retries are performed.
        context: Execution context for logging.
        operation_name: Name of the operation for logging.
        endpoint: The real endpoint URL for sanitization.
        masked_endpoint: The masked endpoint URL for sanitization.

    Returns:
        The result of the function execution.

    Raises:
        The last exception if all retries are exhausted.
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
        ) as e:
            sanitized_error = sanitize_error_message(
                str(e), endpoint or "", masked_endpoint
            )
            if attempt == retry_config.max_retries:
                context.log.error(
                    f"{operation_name} failed after {retry_config.max_retries} retries: {sanitized_error}"
                )
                raise

            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier**attempt),
                retry_config.max_delay,
            )

            if retry_config.jitter:
                delay += random.uniform(0, delay * 0.1)

            context.log.warning(
                f"{operation_name} failed (attempt {attempt + 1}/{retry_config.max_retries + 1}): {sanitized_error}. "
                f"Retrying in {delay:.2f} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError("Retry loop exited without returning or raising")


def execute_with_adaptive_retry(
    func: Callable[[Optional[int]], D],
    retry_config: Optional[RetryConfig],
    context: AssetExecutionContext,
    initial_page_size: Optional[int],
    operation_name: str = "GraphQL operation",
    pagination_context: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None,
    masked_endpoint: Optional[str] = None,
) -> Optional[D]:
    """
    Execute a function with retry mechanism that reduces page size on failures.

    Args:
        func: Function that accepts optional page_size parameter.
        retry_config: Retry configuration with page size reduction.
        context: Execution context for logging.
        initial_page_size: Initial page size to start with.
        operation_name: Name of the operation for logging.
        pagination_context: Optional pagination context for logging.
        endpoint: The real endpoint URL for sanitization.
        masked_endpoint: The masked endpoint URL for sanitization.

    Returns:
        The result of the function execution, or None if continue_on_failure is True and all retries are exhausted.

    Raises:
        The last exception if all retries are exhausted and continue_on_failure is False.
    """
    if not retry_config or not retry_config.reduce_page_size or not initial_page_size:
        return execute_with_retry(
            lambda: func(None),
            retry_config,
            context,
            operation_name,
            endpoint,
            masked_endpoint,
        )

    current_page_size = initial_page_size

    for attempt in range(retry_config.max_retries + 1):
        try:
            context.log.debug(
                f"{operation_name}: Attempting with page_size={current_page_size} (attempt {attempt + 1}/{retry_config.max_retries + 1})"
            )
            result = func(current_page_size)

            if attempt > 0:
                context.log.info(
                    f"{operation_name}: SUCCESS after {attempt} retries with page_size={current_page_size} - resetting to original size {initial_page_size} for next page"
                )
            else:
                context.log.debug(
                    f"{operation_name}: SUCCESS on first attempt with page_size={current_page_size}"
                )

            return result
        except (
            TransportError,
            TransportServerError,
            TransportQueryError,
            ChunkedEncodingError,
        ) as e:
            if attempt == retry_config.max_retries:
                if retry_config.continue_on_failure:
                    log_failure_and_continue(
                        context,
                        operation_name,
                        e,
                        retry_config.max_retries,
                        pagination_metadata={
                            "page_size_at_failure": current_page_size,
                            **(pagination_context or {}),
                        },
                        endpoint=endpoint,
                        masked_endpoint=masked_endpoint,
                    )
                    return None

                context.log.error(
                    f"{operation_name} failed after {retry_config.max_retries} retries: {sanitize_error_message(str(e), endpoint or '', masked_endpoint)}"
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
                    context.log.warning(
                        f"{operation_name}: FAILURE (attempt {attempt + 1}) - reducing page size from {old_page_size} to {current_page_size}"
                    )
                else:
                    context.log.warning(
                        f"{operation_name}: FAILURE (attempt {attempt + 1}) - keeping minimum page size {current_page_size}"
                    )
            else:
                context.log.warning(
                    f"{operation_name}: FAILURE (attempt {attempt + 1}) - keeping page size {current_page_size} (reduction disabled)"
                )

            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier**attempt),
                retry_config.max_delay,
            )

            if retry_config.jitter:
                delay += random.uniform(0, delay * 0.1)

            context.log.warning(
                f"{operation_name}: Retrying in {delay:.2f} seconds... Error: {sanitize_error_message(str(e), endpoint or '', masked_endpoint)}"
            )

            start_sleep = time.time()
            time.sleep(delay)
            actual_delay = time.time() - start_sleep

            context.log.info(
                f"{operation_name}: Waited {actual_delay:.2f} seconds, starting retry attempt {attempt + 2}"
            )

    raise RuntimeError("Retry loop exited without returning or raising")


def extract_data_for_pagination(
    result: Dict[str, Any],
    config: GraphQLResourceConfig,
) -> tuple[List[Any], Optional[Dict[str, Any]]]:
    """
    Extract data and pagination info from the result.

    Returns:
        A tuple of (data_items, pagination_info)
    """
    if config.transform_fn:
        data = config.transform_fn(result)
    else:
        data = result.get(config.target_query, [])

    if not isinstance(data, list):
        if config.pagination and config.pagination.type == PaginationType.RELAY:
            edges = get_nested_value(data, config.pagination.edge_path) or []
            data = [
                get_nested_value(edge, config.pagination.node_path) for edge in edges
            ]
        else:
            data = [data] if data else []

    pagination_info = None
    if config.pagination:
        if config.pagination.type == PaginationType.OFFSET:
            total_count = None
            if config.pagination.total_count_path:
                total_count = get_nested_value(
                    result.get(config.target_query, {}),
                    config.pagination.total_count_path,
                )
            pagination_info = {"total_count": total_count}

        elif config.pagination.type in (PaginationType.CURSOR, PaginationType.RELAY):
            target_data = result.get(config.target_query, {})
            next_cursor = get_nested_value(
                target_data, config.pagination.next_cursor_path
            )
            has_next = get_nested_value(target_data, config.pagination.has_next_path)

            pagination_info = {
                "next_cursor": next_cursor,
                "has_next": has_next,
            }

    return data, pagination_info


Q = ParamSpec("Q")
T = TypeVar("T")

type GraphQLFactoryCallable[**P] = Callable[
    Concatenate[GraphQLResourceConfig, DagsterConfig, AssetExecutionContext, P],
    DltResource,
]


def _graphql_factory(
    _resource: Callable[Q, T],
) -> GraphQLFactoryCallable[Q]:
    """
    This factory creates a DLT asset from a GraphQL resource, automatically
    wiring the introspection query to the target query and generating a Pydantic model.

    Args:
        resource: The function to decorate.
    """

    @functools.wraps(_resource)
    def _factory(
        config: GraphQLResourceConfig,
        global_config: DagsterConfig,
        context: AssetExecutionContext,
        /,
        *_args: Q.args,
        **kwargs: Q.kwargs,
    ):
        """
        Wrap the decorated function with the GraphQLFactory.

        Args:
            config: The configuration for the GraphQL resource.
            global_config: The global dagster configuration.
            context: The execution context for the Dagster asset.
            *_args: The arguments for the decorated function.
            **kwargs: The keyword arguments for the decorated function.

        Returns:
            The DLT asset.
        """

        if not config.target_query or not config.target_query.strip():
            raise ValueError(
                "Target query not specified in the GraphQL resource config."
            )

        if not config.target_type or not config.target_type.strip():
            raise ValueError(
                "Target type not specified in the GraphQL resource config."
            )

        get_graphql_introspection = redis_cache(
            context, global_config.http_cache, _get_graphql_introspection
        )

        @dlt.resource(name=config.name, **kwargs)
        def _execute_query():
            """
            Execute the GraphQL query.

            Returns:
                The GraphQL query result
            """

            headers_tuple = (
                tuple(sorted(config.headers.items())) if config.headers else None
            )
            introspection = get_graphql_introspection(
                config.endpoint, headers_tuple, config.max_depth
            )

            available_types = introspection["__schema"]["types"]
            if not available_types:
                raise ValueError("Malformed introspection query, no types found.")

            dictionary_types = {
                type_obj["name"]: type_obj for type_obj in available_types
            }

            target_object = dictionary_types.get(config.target_type)
            if not target_object:
                raise ValueError(
                    f"Target type '{config.target_type}' not found in the introspection query."
                )

            target_field = next(
                (
                    f
                    for f in target_object.get("fields", [])
                    if f["name"] == config.target_query
                ),
                None,
            )
            if not target_field:
                raise ValueError(
                    f"Target query '{config.target_query}' not found in type '{config.target_type}'."
                )

            type_info = get_type_info(target_field.get("type", {}))
            return_type_name = type_info.get("name")
            if not return_type_name:
                raise ValueError(
                    f"Could not determine return type for query '{config.target_query}'."
                )

            return_type_def = dictionary_types.get(return_type_name)
            if not return_type_def:
                raise ValueError(f"Type '{return_type_name}' not found in schema.")

            field_expander = FieldExpander(
                context,
                dictionary_types,
                config.max_depth,
                config.pagination,
                config.exclude,
            )

            expanded_fields = []
            if return_type_def.get("fields"):
                for field in return_type_def.get("fields", []):
                    expanded = field_expander.expand_field(field, "", 0, "")
                    if expanded:
                        expanded_fields.append(expanded)

            query_parameters, query_variables = get_query_parameters(
                config.parameters, config.pagination
            )

            selection_set = ""
            if expanded_fields:
                selection_set = f" {{ {' '.join(expanded_fields)} }}"
            elif return_type_def.get("kind") == "OBJECT":
                raise ValueError(
                    f"Could not expand any fields for query '{config.target_query}' with return type '{return_type_name}'. "
                    "This might be because all sub-fields require arguments, are excluded, or max_depth is too low."
                )

            generated_body = (
                f"{{ {config.target_query}{query_variables}{selection_set} }}"
            )
            generated_query = f"query {query_parameters} {generated_body}"

            transport = RequestsHTTPTransport(
                url=config.endpoint,
                use_json=True,
                headers=config.headers,
            )

            client = Client(transport=transport)

            if config.masked_endpoint and config.masked_endpoint.strip():
                context.log.info(
                    f"GraphQLFactory: fetching data from {config.masked_endpoint}"
                )
            else:
                context.log.info(
                    f"GraphQLFactory: fetching data from {config.endpoint}"
                )
            context.log.info(f"GraphQLFactory: generated query:\n\n{generated_query}")

            variables = {
                key: param["value"] for key, param in (config.parameters or {}).items()
            }

            has_more = True
            data_items = []

            chunked_load_result = load_chunked_state_and_data(
                config, global_config, context
            )

            yield from chunked_load_result.data_generator

            successful_pages = chunked_load_result.successful_pages
            total_items = chunked_load_result.total_items
            chunked_bucket = chunked_load_result.bucket
            existing_manifest = chunked_load_result.manifest

            variables.update(chunked_load_result.variables_updates)

            while has_more:
                try:
                    original_page_size = (
                        config.pagination.page_size if config.pagination else None
                    )

                    context.log.info(
                        f"GraphQLFactory: Starting page {successful_pages + 1} with original page size {original_page_size}"
                    )

                    def execute_query_with_page_size(
                        page_size: Optional[int] = None,
                    ) -> Dict[str, Any]:
                        query_variables = variables.copy()
                        effective_page_size = page_size or original_page_size

                        if config.pagination:
                            context.log.debug(
                                f"GraphQLFactory: Executing query with page_size={effective_page_size}, offset={total_items}"
                            )

                            if config.pagination.type == PaginationType.OFFSET:
                                query_variables[config.pagination.offset_field] = (
                                    total_items
                                )
                                query_variables[config.pagination.limit_field] = (
                                    effective_page_size
                                )
                            elif config.pagination.type in (
                                PaginationType.CURSOR,
                                PaginationType.RELAY,
                            ):
                                if successful_pages > 0 or query_variables.get(
                                    config.pagination.cursor_field
                                ):
                                    pass
                                else:
                                    query_variables[config.pagination.cursor_field] = (
                                        None
                                    )
                                query_variables[config.pagination.page_size_field] = (
                                    effective_page_size
                                )
                            elif config.pagination.type == PaginationType.KEYSET:
                                query_variables["orderBy"] = (
                                    config.pagination.order_by_field
                                )

                                query_variables["orderDirection"] = (
                                    config.pagination.order_direction
                                )

                                query_variables[config.pagination.page_size_field] = (
                                    effective_page_size
                                )

                                # Initialize where clause if not present
                                query_variables.setdefault("where", {})

                                # For the first page, ensure the initial value is set if not provided
                                if successful_pages == 0:
                                    query_variables["where"].setdefault(
                                        config.pagination.last_value_field, "0"
                                    )

                                context.log.debug(
                                    f"GraphQLFactory: Keyset pagination variables for page {successful_pages + 1}: {query_variables}"
                                )
                        return client.execute(
                            gql(generated_query),
                            variable_values=query_variables,
                        )

                    result = execute_with_adaptive_retry(
                        execute_query_with_page_size,
                        config.retry,
                        context,
                        original_page_size if config.pagination else None,
                        f"GraphQL query execution (page {successful_pages + 1})",
                        pagination_context={
                            "page_number": successful_pages + 1,
                            "total_items_processed": total_items,
                            "successful_pages": successful_pages,
                        },
                        endpoint=config.endpoint,
                        masked_endpoint=config.masked_endpoint,
                    )

                    if result is None:
                        context.log.info(
                            f"GraphQL query execution (page {successful_pages + 1}) failed and was skipped due to continue_on_failure=True"
                        )

                        if config.pagination and config.pagination.type in (
                            PaginationType.CURSOR,
                            PaginationType.RELAY,
                        ):
                            context.log.info(
                                "GraphQLFactory: Cannot continue cursor-based pagination after page failure. Stopping."
                            )
                            break

                        if (
                            config.pagination
                            and config.pagination.type == PaginationType.OFFSET
                        ):
                            original_page_size = config.pagination.page_size
                            total_items += original_page_size
                            context.log.info(
                                f"GraphQLFactory: Advancing offset by {original_page_size} to skip failed page. New offset: {total_items}"
                            )

                        continue

                    data_items, pagination_info = extract_data_for_pagination(
                        result, config
                    )

                    items_in_page = 0
                    if isinstance(data_items, list):
                        items_in_page = len(data_items)
                        for item_idx, item in enumerate(data_items):
                            if config.deps:
                                if item_idx > 0 and config.deps_rate_limit_seconds > 0:
                                    time.sleep(config.deps_rate_limit_seconds)
                                for i, dep in enumerate(config.deps):
                                    if i > 0 and config.deps_rate_limit_seconds > 0:
                                        time.sleep(config.deps_rate_limit_seconds)
                                    yield from dep(context, global_config, item)
                            else:
                                yield item
                    else:
                        items_in_page = 1 if data_items else 0
                        if config.deps:
                            for i, dep in enumerate(config.deps):
                                if i > 0 and config.deps_rate_limit_seconds > 0:
                                    time.sleep(config.deps_rate_limit_seconds)
                                yield from dep(context, global_config, data_items)
                        else:
                            yield data_items

                    total_items += items_in_page
                    successful_pages += 1

                    context.log.info(
                        f"GraphQLFactory: Successfully completed page {successful_pages} with {items_in_page} items (total: {total_items})"
                    )

                    if chunked_bucket:
                        existing_manifest = save_chunked_state_and_data(
                            config,
                            context,
                            data_items,
                            pagination_info,
                            successful_pages,
                            total_items,
                            chunked_bucket,
                            existing_manifest,
                        )

                    if not config.pagination:
                        has_more = False
                    elif config.pagination.stop_condition:
                        has_more = not config.pagination.stop_condition(
                            result, successful_pages
                        )
                        if not has_more:
                            context.log.info("GraphQLFactory: Stop condition met")
                    elif (
                        config.pagination.max_pages
                        and successful_pages >= config.pagination.max_pages
                    ):
                        has_more = False
                        context.log.info(
                            f"GraphQLFactory: Reached max pages limit ({config.pagination.max_pages})"
                        )
                    elif config.pagination.type == PaginationType.OFFSET:
                        if (
                            pagination_info
                            and pagination_info.get("total_count") is not None
                        ):
                            has_more = total_items < pagination_info["total_count"]
                            context.log.debug(
                                f"GraphQLFactory: total_items={total_items}, total_count={pagination_info['total_count']}, has_more={has_more}"
                            )
                        else:
                            has_more = items_in_page > 0
                            context.log.debug(
                                f"GraphQLFactory: No total_count available, has_more={has_more} based on items_in_page={items_in_page}"
                            )
                    elif config.pagination.type in (
                        PaginationType.CURSOR,
                        PaginationType.RELAY,
                    ):
                        if pagination_info:
                            has_more = bool(
                                pagination_info.get("has_next", False)
                                and pagination_info.get("next_cursor")
                            )
                            if has_more:
                                variables[config.pagination.cursor_field] = (
                                    pagination_info["next_cursor"]
                                )
                            context.log.debug(
                                f"GraphQLFactory: Cursor pagination has_more={has_more}"
                            )
                        else:
                            has_more = False
                    elif config.pagination.type == PaginationType.KEYSET:
                        if items_in_page > 0:
                            last_item = data_items[-1]
                            cursor_key = config.pagination.cursor_key
                            if cursor_key in last_item:
                                has_more = True
                                last_value = get_nested_value(
                                    last_item, config.pagination.cursor_key
                                )
                                variables.setdefault("where", {})
                                variables["where"][
                                    config.pagination.last_value_field
                                ] = last_value
                            else:
                                context.log.warning(
                                    f"Pagination cursor key '{cursor_key}' not found in last item of page {successful_pages}. "
                                    "Stopping pagination."
                                )
                                has_more = False
                        else:
                            has_more = False

                    if (
                        has_more
                        and config.pagination
                        and config.pagination.rate_limit_seconds > 0
                    ):
                        context.log.debug(
                            f"GraphQLFactory: Rate limiting for {config.pagination.rate_limit_seconds}s between pages"
                        )
                        time.sleep(config.pagination.rate_limit_seconds)

                except (TransportError, ChunkedEncodingError) as e:
                    sanitized_error = sanitize_error_message(
                        str(e), config.endpoint, config.masked_endpoint
                    )
                    context.log.error(
                        f"GraphQL query execution failed: {sanitized_error}"
                    )
                    raise ValueError(
                        f"Failed to execute GraphQL query: {sanitized_error}"
                    ) from e

            context.log.info(
                f"GraphQLFactory: Completed fetching {total_items} total items across {successful_pages} successful pages"
            )

        return _execute_query

    return cast(GraphQLFactoryCallable[Q], _factory)


graphql_factory = _graphql_factory(dlt.resource)
