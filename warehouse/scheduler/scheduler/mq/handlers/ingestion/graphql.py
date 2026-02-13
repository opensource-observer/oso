import asyncio
from typing import Any, Dict, List, Optional

import dlt
from dlt import pipeline
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from oso_core.graphql.client import (
    GraphQLPaginationExecutor,
    GraphQLQueryBuilder,
    PaginationConfig,
    PaginationType,
    RetryConfig,
)
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from scheduler.config import CommonSettings
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.mq.handlers.ingestion.base import IngestionHandler
from scheduler.types import (
    FailedResponse,
    HandlerResponse,
    RunContext,
    StepContext,
    SuccessResponse,
    TableReference,
)
from scheduler.utils import dlt_to_oso_schema


class GraphQLParameterValue(BaseModel):
    """Value for a GraphQL parameter - text, number, or array."""

    textValue: Optional[str] = None
    numberValue: Optional[float] = None
    arrayValue: Optional[list[str]] = None

    @model_validator(mode="after")
    def validate_exactly_one_value(self):
        """Ensure exactly one of textValue, numberValue, or arrayValue is set."""
        has_text = self.textValue is not None
        has_number = self.numberValue is not None
        has_array = self.arrayValue is not None

        value_count = sum([has_text, has_number, has_array])
        if value_count != 1:
            raise ValueError(
                "Exactly one of textValue, numberValue, or arrayValue must be set"
            )
        return self


class GraphQLParameter(BaseModel):
    """A single GraphQL query parameter from the form schema."""

    name: str
    type: str
    value: GraphQLParameterValue


class GraphQLPaginationConfigModel(BaseModel):
    """Pydantic model for pagination configuration from API."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: str
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

    def to_core_config(self) -> PaginationConfig:
        """Convert to core library PaginationConfig."""
        return PaginationConfig(
            type=PaginationType(self.type.lower()),
            page_size=self.page_size,
            max_pages=self.max_pages,
            rate_limit_seconds=self.rate_limit_seconds,
            offset_field=self.offset_field,
            limit_field=self.limit_field,
            total_count_path=self.total_count_path,
            cursor_field=self.cursor_field,
            page_size_field=self.page_size_field,
            next_cursor_path=self.next_cursor_path,
            has_next_path=self.has_next_path,
            edge_path=self.edge_path,
            node_path=self.node_path,
            order_by_field=self.order_by_field,
            last_value_field=self.last_value_field,
            cursor_key=self.cursor_key,
            order_direction=self.order_direction,
        )


class GraphQLRetryConfigModel(BaseModel):
    """Pydantic model for retry configuration from API."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    reduce_page_size: bool = True
    min_page_size: int = 10
    page_size_reduction_factor: float = 0.5
    continue_on_failure: bool = False

    def to_core_config(self) -> RetryConfig:
        """Convert to core library RetryConfig."""
        return RetryConfig(
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            backoff_multiplier=self.backoff_multiplier,
            jitter=self.jitter,
            reduce_page_size=self.reduce_page_size,
            min_page_size=self.min_page_size,
            page_size_reduction_factor=self.page_size_reduction_factor,
            continue_on_failure=self.continue_on_failure,
        )


class GraphQLConfigModel(BaseModel):
    """Pydantic model for GraphQL configuration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    endpoint: str
    target_type: str
    target_query: str
    max_depth: int = 5
    headers: Optional[Dict[str, str]] = None
    parameters: Optional[List[GraphQLParameter]] = None
    pagination: Optional[GraphQLPaginationConfigModel] = None
    exclude: Optional[List[str]] = None
    retry: Optional[GraphQLRetryConfigModel] = None


class GraphQLIngestionHandler(IngestionHandler):
    """Handler for GraphQL data ingestion using core GraphQL client."""

    async def execute(
        self,
        context: RunContext,
        step_context: StepContext,
        config: dict[str, object],
        dataset_id: str,
        org_id: str,
        dlt_destination: DLTDestinationResource,
        common_settings: CommonSettings,
    ) -> HandlerResponse:
        """Execute GraphQL data ingestion."""

        try:
            try:
                graphql_config = GraphQLConfigModel.model_validate(config)
            except ValidationError as e:
                error_msg = f"Invalid GraphQL config: {e.errors()}"
                step_context.log.error(
                    "Invalid GraphQL config", extra={"errors": e.errors()}
                )
                return FailedResponse(message=error_msg)

            normalized_parameters: Optional[Dict[str, Dict[str, Any]]] = None
            if graphql_config.parameters:
                normalized_parameters = {
                    p.name: {
                        "type": p.type,
                        "value": p.value.textValue
                        or p.value.numberValue
                        or p.value.arrayValue,
                    }
                    for p in graphql_config.parameters
                }

            step_context.log.info(
                "Starting GraphQL data ingestion",
                extra={
                    "dataset_id": dataset_id,
                    "endpoint": graphql_config.endpoint,
                    "target_query": graphql_config.target_query,
                },
            )

            pagination_config = None
            if graphql_config.pagination:
                core_config = graphql_config.pagination.to_core_config()
                pagination_config = (
                    None if core_config.type == PaginationType.NONE else core_config
                )

            retry_config = None
            if graphql_config.retry:
                retry_config = graphql_config.retry.to_core_config()

            step_context.log.info(
                "Building GraphQL query from schema introspection",
                extra={
                    "exclude_fields": graphql_config.exclude,
                },
            )

            headers_tuple = (
                tuple(sorted(graphql_config.headers.items()))
                if graphql_config.headers
                else None
            )

            query_builder = GraphQLQueryBuilder(step_context.log)
            try:
                generated_query = query_builder.build_query(
                    endpoint=graphql_config.endpoint,
                    headers_tuple=headers_tuple,
                    target_type=graphql_config.target_type,
                    target_query=graphql_config.target_query,
                    max_depth=graphql_config.max_depth,
                    parameters=normalized_parameters,
                    pagination_config=pagination_config,
                    exclude_fields=graphql_config.exclude,
                )
            except ValueError as e:
                return FailedResponse(message=str(e))

            step_context.log.info(
                "Generated GraphQL query", extra={"query": generated_query}
            )

            transport = RequestsHTTPTransport(
                url=graphql_config.endpoint,
                use_json=True,
                headers=graphql_config.headers,
            )
            client = Client(transport=transport)

            @dlt.resource(name=graphql_config.target_query, write_disposition="replace")
            def graphql_resource():
                """DLT resource that fetches data from GraphQL API."""
                initial_variables = {
                    key: param["value"]
                    for key, param in (normalized_parameters or {}).items()
                }

                executor = GraphQLPaginationExecutor(
                    client=client,
                    logger=step_context.log,
                    pagination_config=pagination_config,
                    retry_config=retry_config,
                    endpoint=graphql_config.endpoint,
                    masked_endpoint=None,
                )

                yield from executor.execute_paginated_query(
                    generated_query=generated_query,
                    initial_variables=initial_variables,
                    transform_fn=None,
                    target_query=graphql_config.target_query,
                    initial_page_number=0,
                    initial_total_items=0,
                )

            placeholder_target_table = step_context.generate_destination_table_exp(
                TableReference(
                    org_id=org_id,
                    dataset_id=dataset_id,
                    table_id="placeholder_table",
                )
            )

            dataset_schema = placeholder_target_table.db
            pipeline_name = f"{org_id}_{dataset_id}".replace("-", "")[:50]

            async with dlt_destination.get_destination(
                dataset_schema=dataset_schema
            ) as destination:
                p = pipeline(
                    pipeline_name=pipeline_name,
                    dataset_name=dataset_schema,
                    destination=destination,
                    pipelines_dir=common_settings.local_working_dir,
                )

                step_context.log.info(
                    "Running dlt pipeline",
                    extra={
                        "pipeline_name": pipeline_name,
                        "dataset_schema": dataset_schema,
                    },
                )

                load_info = await asyncio.to_thread(p.run, graphql_resource)

            step_context.log.info(
                "Data ingestion completed successfully",
                extra={
                    "pipeline_name": pipeline_name,
                    "loaded_packages": len(load_info.loads_ids) if load_info else 0,
                },
            )

            tables = p.default_schema.data_tables()

            step_context.log.info(
                "Creating materializations for ingested tables",
                extra={
                    "num_tables": len(tables),
                    "dataset_id": dataset_id,
                },
            )

            for table in tables:
                table_name = table.get("name")
                if not table_name:
                    step_context.log.warning(
                        "Skipping table without name",
                        extra={"table": table},
                    )
                    continue

                schema = dlt_to_oso_schema(table.get("columns"))

                warehouse_fqn = f"{common_settings.warehouse_shared_catalog_name}.{dataset_schema}.{table_name}"

                await step_context.create_materialization(
                    table_id=f"data_ingestion_{table_name}",
                    warehouse_fqn=warehouse_fqn,
                    schema=schema,
                )

                step_context.log.info(
                    "Created materialization",
                    extra={
                        "table_name": table_name,
                        "warehouse_fqn": warehouse_fqn,
                    },
                )

        except Exception as e:
            step_context.log.error(
                "GraphQL data ingestion failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            return FailedResponse(message=f"GraphQL data ingestion failed: {e}")

        return SuccessResponse(message="GraphQL data ingestion completed successfully")
