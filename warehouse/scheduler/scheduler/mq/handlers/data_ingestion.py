import uuid

import structlog
from dlt import pipeline
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from osoprotobufs.data_ingestion_pb2 import DataIngestionRunRequest
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.enums import RunStatus
from scheduler.graphql_client.get_data_ingestion_config import (
    GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestion,
)
from scheduler.types import MessageHandler

logger = structlog.getLogger(__name__)


def format_uuid_from_bytes(uuid_bytes: bytes) -> str:
    """Convert bytes to UUID string."""
    return str(uuid.UUID(bytes=uuid_bytes))


class DataIngestionRunRequestHandler(MessageHandler[DataIngestionRunRequest]):
    topic = "data_ingestion_run_requests"
    message_type = DataIngestionRunRequest
    schema_file_name = "data-ingestion.proto"

    async def handle_message(
        self,
        *,
        message: DataIngestionRunRequest,
        oso_client: Client,
        **_kwargs,
    ) -> None:
        run_id_bytes = bytes(message.run_id)
        config_id_bytes = bytes(message.config_id)
        dataset_id = message.dataset_id

        run_id = format_uuid_from_bytes(run_id_bytes)
        config_id = format_uuid_from_bytes(config_id_bytes)

        logger.info(
            "Received DataIngestionRunRequest",
            run_id=run_id,
            dataset_id=dataset_id,
            config_id=config_id,
        )

        try:
            config_response = await oso_client.get_data_ingestion_config(
                dataset_id=dataset_id,
                config_id=config_id,
            )
        except Exception as e:
            logger.error("Failed to fetch config", run_id=run_id, error=str(e))
            await self._mark_failed(oso_client, run_id, f"Config fetch failed: {e}")
            return

        edges = config_response.datasets.edges
        if not edges or not edges[0].node.type_definition:
            logger.error("Config not found", run_id=run_id, config_id=config_id)
            await self._mark_failed(oso_client, run_id, "Config not found")
            return

        type_def = edges[0].node.type_definition

        if not isinstance(
            type_def,
            GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestion,
        ):
            logger.error(
                "Dataset is not a DataIngestion type",
                run_id=run_id,
                type=type_def.typename__,
            )
            await self._mark_failed(
                oso_client, run_id, f"Wrong dataset type: {type_def.typename__}"
            )
            return

        if not type_def.configs.edges:
            logger.error("No configs found", run_id=run_id)
            await self._mark_failed(oso_client, run_id, "Config not found")
            return

        config = type_def.configs.edges[0].node

        if config.factory_type != "REST":
            logger.error(
                "Unsupported factory type",
                run_id=run_id,
                factory_type=config.factory_type,
            )
            await self._mark_failed(
                oso_client, run_id, f"Unsupported type: {config.factory_type}"
            )
            return

        logger.info(
            "Config validated",
            run_id=run_id,
            config_id=config_id,
            factory_type=config.factory_type,
        )

        try:
            rest_api_config: RESTAPIConfig = config.config

            logger.info(
                "Creating REST API resources",
                run_id=run_id,
                num_endpoints=len(rest_api_config.get("resources", [])),
            )

            resources = rest_api_resources(rest_api_config)

            pipeline_name = f"data_ingestion_{dataset_id}_{config_id}"[:50]
            p = pipeline(
                pipeline_name=pipeline_name,
                dataset_name=dataset_id.replace("-", "_"),
                destination="duckdb",
            )

            logger.info(
                "Running dlt pipeline", run_id=run_id, pipeline_name=pipeline_name
            )

            load_info = p.run(resources)

            logger.info(
                "Data ingestion completed successfully",
                run_id=run_id,
                pipeline_name=pipeline_name,
                loaded_packages=len(load_info.loads_ids) if load_info else 0,
            )

            await oso_client.finish_run(
                run_id=run_id,
                status=RunStatus.SUCCESS,
                logs_url="",
            )
            logger.info("Run completed", run_id=run_id)

        except Exception as e:
            logger.error(
                "Data ingestion failed", run_id=run_id, error=str(e), exc_info=True
            )
            await self._mark_failed(oso_client, run_id, f"Execution error: {e}")
            return

    async def _mark_failed(self, oso_client: Client, run_id: str, message: str):
        try:
            await oso_client.finish_run(
                run_id=run_id,
                status=RunStatus.FAILED,
                logs_url="",
            )
            logger.info("Marked as failed", run_id=run_id, message=message)
        except Exception as e:
            logger.error("Failed to mark as failed", run_id=run_id, error=str(e))
