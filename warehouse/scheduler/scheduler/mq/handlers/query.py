import json
import typing as t

import aiotrino
import aiotrino.utils
import structlog
from aioprometheus.collectors import Counter, Summary
from aiotrino.exceptions import (
    TrinoExternalError,
    TrinoUserError,
)
from duckdb import ProgrammingError
from oso_core.instrumentation.common import MetricsLabeler
from oso_core.instrumentation.container import MetricsContainer
from oso_core.instrumentation.timing import async_time
from oso_dagster.resources import GCSFileResource, TrinoResource
from osoprotobufs.query_pb2 import QueryRunRequest
from queryrewriter import rewrite_query
from queryrewriter.errors import TableResolutionError
from queryrewriter.types import TableResolver
from scheduler.graphql_client.client import Client
from scheduler.mq.common import RunHandler, convert_uuid_bytes_to_str
from scheduler.types import FailedResponse, HandlerResponse, RunContext, SuccessResponse
from scheduler.utils import OSOClientTableResolver, aiotrino_query_error_to_json

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings

logger = structlog.getLogger(__name__)


class QueryRunRequestHandler(RunHandler[QueryRunRequest]):
    topic = "query_run_requests"
    message_type = QueryRunRequest
    schema_file_name = "query.proto"

    def initialize(self, metrics: MetricsContainer):
        metrics.initialize_counter(
            Counter(
                "query_response_total", "Total number of query responses processed"
            ),
        )
        metrics.initialize_summary(
            Summary(
                "query_row_count",
                "Number of rows returned by queries",
            ),
        )
        metrics.initialize_summary(
            Summary(
                "query_duration_ms",
                "Duration of query execution in milliseconds",
            )
        )
        return super().initialize(metrics=metrics)

    async def handle_run_message(
        self,
        common_settings: "CommonSettings",
        context: RunContext,
        message: QueryRunRequest,
        consumer_trino: TrinoResource,
        gcs: GCSFileResource,
        oso_client: Client,
        metrics: MetricsContainer,
    ) -> HandlerResponse:
        # Process the QueryRunRequest message
        context.log.info(f"Handling QueryRunRequest with ID: {message.run_id}")

        table_resolvers: list[TableResolver] = [
            OSOClientTableResolver(oso_client=oso_client)
        ]

        context.log.info(f"Executing query: {message.query}")

        logger.info(f"User: {message.user}")
        logger.info(f"Query: {message.query}")

        labeler = MetricsLabeler()
        requested_by = "system"
        if context.trigger_type == "user":
            if context.requested_by:
                requested_by = context.requested_by.id
            else:
                requested_by = "unknown"

        labeler.set_labels(
            {
                "org_id": context.organization.id,
                "trigger_type": context.trigger_type,
                "requested_by": requested_by,
                "contains_udm_reference": "unknown",
            }
        )

        try:
            query = await rewrite_query(message.query, table_resolvers)
        except TableResolutionError as e:
            logger.error(f"Table resolution error: {e}")

            metrics.counter("query_response_total").inc(
                labeler.get_labels(
                    {
                        "response_type": "table_resolution_error",
                        "response_code": "404",
                    }
                )
            )
            return FailedResponse(
                message=f"Table resolution error for QueryRunRequest ID: {message.run_id}",
                status_code=404,
                details={
                    "message": str(e),
                    # Match the error types used in trino
                    "error_type": "USER_ERROR",
                    "error_name": "TablesNotFound",
                },
            )

        # Check if the rewritten tables use UDMs if so we disable caching by setting
        # a metadata boolean `containsUdmReference` to true
        contains_udm_reference = False
        for table in query.tables.values():
            if table.startswith(common_settings.warehouse_shared_catalog_name):
                contains_udm_reference = True
                break

        if contains_udm_reference:
            await context.update_metadata({"containsUdmReference": True}, merge=True)

        labeler.add_labels(
            {
                "contains_udm_reference": str(contains_udm_reference).lower(),
            }
        )

        logger.info(f"Rewritten Query: {query.rewritten_query}")

        storage_client = gcs.get_client(asynchronous=False)
        async with consumer_trino.async_get_client(user=message.user) as client:
            cursor = await client.cursor()
            try:
                cursor = await cursor.execute(query.rewritten_query)
            except TrinoUserError as e:
                logger.error(f"Error executing query: {e}")
                metrics.counter("query_response_total").inc(
                    labeler.get_labels(
                        {
                            "response_type": "trino_user_error",
                            "response_code": "400",
                        }
                    )
                )
                return FailedResponse(
                    message=f"Failed to execute query for QueryRunRequest ID: {message.run_id}",
                    status_code=400,
                    details=aiotrino_query_error_to_json(e),
                )
            except TrinoExternalError as e:
                logger.error(f"Server error while executing query: {e}")

                metrics.counter("query_response_total").inc(
                    labeler.get_labels(
                        {
                            "response_type": "trino_external_error",
                            "response_code": "500",
                        }
                    )
                )
                return FailedResponse(
                    message=f"Server error for QueryRunRequest ID: {message.run_id}",
                    status_code=500,
                    details=aiotrino_query_error_to_json(e),
                )
            # This will handle errors for other dbapi exceptions so
            # we can remain compatible with duckdb as well
            except ProgrammingError as e:
                logger.error(f"Programming error while executing query: {e}")
                metrics.counter("query_response_total").inc(
                    labeler.get_labels(
                        {
                            "response_type": "programming_error",
                            "response_code": "400",
                        }
                    )
                )
                return FailedResponse(
                    message=f"Programming error for QueryRunRequest ID: {message.run_id}",
                    status_code=400,
                    details={
                        "message": f"Programming error in query execution. {e}",
                        "error_type": "ProgrammingError",
                        "error_name": "ProgrammingError",
                    },
                )
            except Exception as e:
                logger.error(f"Unexpected error while executing query: {e}")
                metrics.counter("query_response_total").inc(
                    labeler.get_labels(
                        {
                            "response_type": "unknown_error",
                            "response_code": "500",
                        }
                    )
                )
                return FailedResponse(
                    message=f"Unexpected error for QueryRunRequest ID: {message.run_id}",
                    status_code=500,
                    details={
                        "message": str(e),
                        "error_type": "UnknownError",
                        "error_name": "UnknownError",
                    },
                )

            columns = [column.name for column in await cursor.get_description()]
            file_path = f"gs://{common_settings.query_bucket}/{convert_uuid_bytes_to_str(message.run_id)}"
            logger.info(f"Writing query results to: {file_path}")

            row_count = 0

            async with async_time(metrics.summary("query_duration_ms"), labeler):
                with storage_client.open(
                    file_path,
                    "w",
                    encoding="utf-8",
                    compression="gzip",
                    content_type="application/jsonl",
                    fixed_key_metadata={"content_encoding": "gzip"},
                ) as f:
                    f.write(json.dumps(columns) + "\n")
                    print("Columns:", columns)
                    async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                        print("Row???:", row)
                        if row is None:
                            continue
                        row_count += 1
                        f.write(json.dumps(row, default=str) + "\n")

                metrics.summary("query_row_count").observe(
                    labeler.get_labels(), row_count
                )
        logger.info("Query results written successfully")
        metrics.counter("query_response_total").inc(
            labeler.get_labels(
                {
                    "response_type": "success",
                    "response_code": "200",
                }
            ),
        )
        return SuccessResponse(
            message=f"Processed QueryRunRequest with ID: {message.run_id}"
        )
