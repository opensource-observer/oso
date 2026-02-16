import asyncio
from typing import List, Tuple

import aiotrino.dbapi
import aiotrino.utils
from oso_dagster.resources.trino import TrinoResource
from osoprotobufs.sync_connection_pb2 import SyncConnectionRunRequest
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.input_types import (
    DataConnectionSchemaInput,
    DataConnectionTableInput,
    DataModelColumnInput,
)
from scheduler.mq.common import RunHandler
from scheduler.types import (
    FailedResponse,
    HandlerResponse,
    RunContext,
    SuccessResponse,
)
from scheduler.utils import get_warehouse_user

EXCLUDED_SCHEMAS = {"information_schema"}
MAX_CONCURRENT_QUERIES = 5  # Number of concurrent queries to run


async def fetch_tables_for_schema(
    context: RunContext,
    client: aiotrino.dbapi.Connection,
    catalog_name: str,
    schema_name: str,
    semaphore: asyncio.Semaphore,
) -> Tuple[str, List[str]]:
    """Fetch all tables for a given schema."""
    async with semaphore:
        try:
            cursor = await client.cursor()
            await cursor.execute(f'SHOW TABLES FROM "{catalog_name}"."{schema_name}"')
            table_names = []
            async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                if row:
                    table_names.append(row[0])

            context.log.info(
                "Found tables",
                extra={"schema": schema_name, "table_count": len(table_names)},
            )
            return schema_name, table_names
        except Exception as e:
            context.log.error(
                "Failed to get tables",
                extra={"schema": schema_name, "error": str(e)},
            )
            return schema_name, []


async def fetch_columns_for_table(
    context: RunContext,
    client: aiotrino.dbapi.Connection,
    catalog_name: str,
    schema_name: str,
    table_name: str,
    semaphore: asyncio.Semaphore,
) -> Tuple[str, str, List[DataModelColumnInput]]:
    """Fetch all columns for a given table."""
    async with semaphore:
        try:
            cursor = await client.cursor()
            await cursor.execute(
                f'SHOW COLUMNS FROM "{catalog_name}"."{schema_name}"."{table_name}"'
            )
            columns = []
            async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                if row:
                    columns.append(DataModelColumnInput(name=row[0], type=row[1]))

            context.log.info(
                "Collected table schema",
                extra={
                    "schema": schema_name,
                    "table": table_name,
                    "column_count": len(columns),
                },
            )
            return schema_name, table_name, columns
        except Exception as e:
            context.log.error(
                "Failed to get columns",
                extra={
                    "schema": schema_name,
                    "table": table_name,
                    "error": str(e),
                },
            )
            return schema_name, table_name, []


class SyncConnectionRunRequestHandler(RunHandler[SyncConnectionRunRequest]):
    topic = "sync_connection_run_requests"
    message_type = SyncConnectionRunRequest
    schema_file_name = "sync-connection.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        message: SyncConnectionRunRequest,
        consumer_trino: TrinoResource,
        oso_client: Client,
    ) -> HandlerResponse:
        connection_id = message.connection_id

        context.log.info(
            "Received SyncConnectionRunRequest",
            extra={"connection_id": connection_id},
        )

        # Step 1: Get data connection info
        try:
            dc_response = await oso_client.get_data_connection(connection_id)
            edges = dc_response.data_connections.edges
            if not edges:
                return FailedResponse(
                    message=f"Data connection {connection_id} not found"
                )

            data_connection = edges[0].node
            organization = data_connection.organization
            catalog_name = f"org_{organization.id.replace('-', '').lower()}_{data_connection.name.lower()}"
        except Exception as e:
            context.log.error("Failed to get data connection", extra={"error": str(e)})
            return FailedResponse(
                exception=e,
                message="Failed to get data connection",
                details={"error": str(e)},
            )

        context.log.info(
            "Found data connection",
            extra={"catalog_name": catalog_name, "org_id": organization.id},
        )

        user = get_warehouse_user("ro", organization.id, organization.name)

        # Use a single Trino client for all queries
        async with consumer_trino.async_get_client(user=user) as client:
            # Get all schemas
            try:
                cursor = await client.cursor()
                await cursor.execute(f'SHOW SCHEMAS FROM "{catalog_name}"')
                schemas = []
                async for row in aiotrino.utils.aiter(cursor.fetchone, None):
                    if row and row[0] not in EXCLUDED_SCHEMAS:
                        schemas.append(row[0])
            except Exception as e:
                context.log.error("Failed to get schemas", extra={"error": str(e)})
                return FailedResponse(
                    exception=e,
                    message="Failed to get schemas from catalog",
                    details={"error": str(e)},
                )

            context.log.info(
                "Found schemas",
                extra={"schema_count": len(schemas), "schemas": schemas},
            )

            # Fetch tables for all schemas concurrently
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)
            table_tasks = [
                fetch_tables_for_schema(
                    context, client, catalog_name, schema_name, semaphore
                )
                for schema_name in schemas
            ]
            schema_tables = await asyncio.gather(*table_tasks)

            # Build list of all column fetch tasks
            column_tasks = []
            for schema_name, table_names in schema_tables:
                for table_name in table_names:
                    column_tasks.append(
                        fetch_columns_for_table(
                            context,
                            client,
                            catalog_name,
                            schema_name,
                            table_name,
                            semaphore,
                        )
                    )

            # Fetch columns for all tables concurrently
            context.log.info(
                "Fetching columns for all tables",
                extra={"total_tables": len(column_tasks)},
            )
            table_columns = await asyncio.gather(*column_tasks)

            # Organize results by schema
            schema_table_map = {}
            for schema_name, table_name, columns in table_columns:
                if columns:  # Only include tables with columns
                    if schema_name not in schema_table_map:
                        schema_table_map[schema_name] = []
                    schema_table_map[schema_name].append(
                        DataConnectionTableInput(name=table_name, schema=columns)
                    )

            # Build schema inputs
            schema_inputs = [
                DataConnectionSchemaInput(name=schema_name, tables=tables)
                for schema_name, tables in schema_table_map.items()
                if tables  # Only include schemas with tables
            ]

        # Create all datasets, aliases, and materializations in one batch
        if schema_inputs:
            try:
                context.log.info(
                    "Creating datasets and materializations",
                    extra={"schema_count": len(schema_inputs)},
                )

                await oso_client.create_data_connection_datasets(
                    run_id=context.run_id,
                    org_id=organization.id,
                    data_connection_id=connection_id,
                    schemas=schema_inputs,
                )

                context.log.info(
                    "Successfully created all datasets and materializations"
                )
            except Exception as e:
                context.log.error(
                    "Failed to create datasets",
                    extra={"error": str(e)},
                )
                return FailedResponse(
                    exception=e,
                    message="Failed to create datasets and materializations",
                    details={"error": str(e)},
                )
        else:
            context.log.warning("No schemas with tables found to sync")

        return SuccessResponse(message="Sync connection completed successfully")
