import csv
import typing as t

import aiotrino
import aiotrino.utils
import structlog
from oso_dagster.resources import GCSFileResource, TrinoResource
from osoprotobufs.query_pb2 import QueryRunRequest
from queryrewriter import rewrite_query
from queryrewriter.types import TableResolver
from scheduler.graphql_client.client import Client
from scheduler.mq.common import RunHandler, convert_uuid_bytes_to_str
from scheduler.types import HandlerResponse, RunContext, SuccessResponse
from scheduler.utils import OSOClientTableResolver

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

        logger.info(f"Query: {message.query}")
        query = await rewrite_query(message.query, table_resolvers)
        logger.info(f"Rewritten Query: {query.rewritten_query}")

        storage_client = gcs.get_client(asynchronous=False)
        try:
            async with consumer_trino.async_get_client(jwt_token=message.jwt) as client:
                cursor = await client.cursor()
                cursor = await cursor.execute(query.rewritten_query)
                columns = (column.name for column in await cursor.get_description())
                with storage_client.open(
                    f"gs://{common_settings.query_bucket}/{convert_uuid_bytes_to_str(message.run_id)}",
                    "w",
                    encoding="utf-8",
                    compression="gzip",
                    content_type="text/csv",
                    fixed_key_metadata={"content_encoding": "gzip"},
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                        if row is None:
                            continue
                        writer.writerow(row)

            return SuccessResponse(
                message=f"Processed QueryRunRequest with ID: {message.run_id}"
            )
        finally:
            if storage_client.session:
                await storage_client.session.close()
