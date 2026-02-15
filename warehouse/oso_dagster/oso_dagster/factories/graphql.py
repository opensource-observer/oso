import functools
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Concatenate,
    Dict,
    Generator,
    List,
    Optional,
    ParamSpec,
    TypeVar,
    cast,
)

import dlt
from dagster import AssetExecutionContext, AssetObservation, MetadataValue
from dlt.extract.resource import DltResource
from google.cloud import storage
from google.cloud.exceptions import NotFound
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from oso_core.graphql.client import (
    GraphQLPaginationExecutor,
    GraphQLPaginationState,
    GraphQLQueryBuilder,
    PaginationConfig,
    PaginationType,
    RetryConfig,
    get_graphql_introspection,
    sanitize_error_message,
)
from oso_dagster.config import DagsterConfig
from oso_dagster.utils.redis import redis_cache

type GraphQLDependencyCallable = Callable[
    [AssetExecutionContext, DagsterConfig, Any], Generator[DltResource, Any, Any]
]


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

        cached_get_graphql_introspection = redis_cache(
            context, global_config.http_cache, get_graphql_introspection
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

            query_builder = GraphQLQueryBuilder(
                context.log, introspection_fetcher=cached_get_graphql_introspection
            )

            generated_query = query_builder.build_query(
                endpoint=config.endpoint,
                headers_tuple=headers_tuple,
                target_type=config.target_type,
                target_query=config.target_query,
                max_depth=config.max_depth,
                parameters=config.parameters,
                pagination_config=config.pagination,
                exclude_fields=config.exclude,
            )

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

            chunked_load_result = load_chunked_state_and_data(
                config, global_config, context
            )

            yield from chunked_load_result.data_generator

            initial_variables = {
                key: param["value"] for key, param in (config.parameters or {}).items()
            }
            initial_variables.update(chunked_load_result.variables_updates)

            chunked_bucket = chunked_load_result.bucket
            existing_manifest = chunked_load_result.manifest

            def save_chunk_callback(
                data_items: List[Any],
                pagination_info: Optional[Dict[str, Any]],
                successful_pages: int,
                total_items: int,
            ) -> None:
                """Callback to save chunks after each successful page."""
                nonlocal existing_manifest
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

            executor = GraphQLPaginationExecutor(
                client=client,
                logger=context.log,
                pagination_config=config.pagination,
                retry_config=config.retry,
                endpoint=config.endpoint,
                masked_endpoint=config.masked_endpoint,
            )

            for item in executor.execute_paginated_query(
                generated_query=generated_query,
                initial_variables=initial_variables,
                transform_fn=config.transform_fn,
                target_query=config.target_query,
                initial_page_number=chunked_load_result.successful_pages,
                initial_total_items=chunked_load_result.total_items,
                page_callback=save_chunk_callback if chunked_bucket else None,
            ):
                if config.deps:
                    for dep_idx, dep in enumerate(config.deps):
                        if dep_idx > 0 and config.deps_rate_limit_seconds > 0:
                            time.sleep(config.deps_rate_limit_seconds)
                        yield from dep(context, global_config, item)
                else:
                    yield item

        return _execute_query

    return cast(GraphQLFactoryCallable[Q], _factory)


graphql_factory = _graphql_factory(dlt.resource)
