import json
import typing as t

import aiotrino
import aiotrino.utils
import structlog
from aiotrino.exceptions import (
    TrinoExternalError,
    TrinoUserError,
)
from oso_dagster.resources import GCSFileResource, TrinoResource
from osoprotobufs.query_pb2 import QueryRunRequest
from queryrewriter import rewrite_query
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

    async def handle_run_message(
        self,
        common_settings: "CommonSettings",
        context: RunContext,
        message: QueryRunRequest,
        consumer_trino: TrinoResource,
        gcs: GCSFileResource,
        oso_client: Client,
    ) -> HandlerResponse:
        # Process the QueryRunRequest message
        context.log.info(f"Handling QueryRunRequest with ID: {message.run_id}")

        table_resolvers: list[TableResolver] = [
            OSOClientTableResolver(oso_client=oso_client)
        ]

        context.log.info(f"Executing query: {message.query}")

        logger.info(f"User: {message.user}")
        logger.info(f"Query: {message.query}")
        query = await rewrite_query(message.query, table_resolvers)
        # Check if the rewritten tables use UDMs if so we disable caching by setting
        # a metadata boolean `containsUdmReference` to true
        contains_udm_reference = False
        for table in query.tables.values():
            if table.startswith(common_settings.warehouse_shared_catalog_name):
                contains_udm_reference = True
                break
        if contains_udm_reference:
            await context.update_metadata({"containsUdmReference": True}, merge=True)

        logger.info(f"Rewritten Query: {query.rewritten_query}")

        storage_client = gcs.get_client(asynchronous=False)
        async with consumer_trino.async_get_client(user=message.user) as client:
            cursor = await client.cursor()
            try:
                cursor = await cursor.execute(query.rewritten_query)
            except TrinoUserError as e:
                logger.error(f"Error executing query: {e}")
                return FailedResponse(
                    message=f"Failed to execute query for QueryRunRequest ID: {message.run_id}",
                    status_code=400,
                    details=aiotrino_query_error_to_json(e),
                )
            except TrinoExternalError as e:
                logger.error(f"Server error while executing query: {e}")
                return FailedResponse(
                    message=f"Server error for QueryRunRequest ID: {message.run_id}",
                    status_code=500,
                    details=aiotrino_query_error_to_json(e),
                )

            columns = [column.name for column in await cursor.get_description()]
            file_path = f"gs://{common_settings.query_bucket}/{convert_uuid_bytes_to_str(message.run_id)}"
            logger.info(f"Writing query results to: {file_path}")
            with storage_client.open(
                file_path,
                "w",
                encoding="utf-8",
                compression="gzip",
                content_type="application/jsonl",
                fixed_key_metadata={"content_encoding": "gzip"},
            ) as f:
                f.write(json.dumps(columns) + "\n")
                async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                    if row is None:
                        continue
                    f.write(json.dumps(row, default=str) + "\n")
        logger.info("Query results written successfully")
        return SuccessResponse(
            message=f"Processed QueryRunRequest with ID: {message.run_id}"
        )
