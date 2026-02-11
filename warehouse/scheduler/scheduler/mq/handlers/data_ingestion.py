from osoprotobufs.data_ingestion_pb2 import DataIngestionRunRequest
from scheduler.config import CommonSettings
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.get_data_ingestion_config import (
    GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestionDefinition,
)
from scheduler.mq.common import RunHandler
from scheduler.mq.handlers.ingestion import (
    ArchiveIngestionHandler,
    IngestionHandler,
    RestIngestionHandler,
)
from scheduler.types import (
    FailedResponse,
    HandlerResponse,
    RunContext,
)


class DataIngestionRunRequestHandler(RunHandler[DataIngestionRunRequest]):
    topic = "data_ingestion_run_requests"
    message_type = DataIngestionRunRequest
    schema_file_name = "data-ingestion.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        message: DataIngestionRunRequest,
        oso_client: Client,
        dlt_destination: DLTDestinationResource,
        common_settings: CommonSettings,
    ) -> HandlerResponse:
        dataset_id = message.dataset_id

        context.log.info(
            "Received DataIngestionRunRequest",
            extra={
                "dataset_id": dataset_id,
            },
        )

        try:
            config_response = await oso_client.get_data_ingestion_config(
                dataset_id=dataset_id,
            )
        except Exception as e:
            context.log.error(
                "Failed to fetch config",
                extra={
                    "dataset_id": dataset_id,
                    "error": str(e),
                },
            )
            return FailedResponse(message=f"Config fetch failed: {e}")

        edges = config_response.datasets.edges
        if not edges or not edges[0].node.type_definition:
            context.log.error("Config not found", extra={"dataset_id": dataset_id})
            return FailedResponse(message="Config not found")

        node = edges[0].node
        type_def = node.type_definition
        org_id = node.organization.id

        if not isinstance(
            type_def,
            GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestionDefinition,
        ):
            context.log.error(
                "Dataset is not a DataIngestionDefinition type",
                extra={"type": type_def.typename__},
            )
            return FailedResponse(message=f"Wrong dataset type: {type_def.typename__}")

        config = type_def.data_ingestion

        if not config:
            context.log.error(
                "No data ingestion configuration found",
                extra={"dataset_id": dataset_id},
            )
            return FailedResponse(message="No data ingestion configuration found")

        context.log.info(
            "Config validated",
            extra={
                "dataset_id": dataset_id,
                "config_id": config.id,
                "factory_type": config.factory_type,
            },
        )

        handlers: dict[str, IngestionHandler] = {
            "REST": RestIngestionHandler(),
            "ARCHIVE_DIR": ArchiveIngestionHandler(),
        }

        handler = handlers.get(config.factory_type)
        if not handler:
            context.log.error(
                "Unsupported factory type",
                extra={"factory_type": config.factory_type},
            )
            return FailedResponse(
                message=f"Unsupported type: {config.factory_type}",
            )

        async with context.step_context(
            name="execute_data_ingestion_pipeline",
            display_name="Execute Data Ingestion Pipeline",
        ) as step_context:
            return await handler.execute(
                context=context,
                step_context=step_context,
                config=config.config,
                dataset_id=dataset_id,
                org_id=org_id,
                dlt_destination=dlt_destination,
                common_settings=common_settings,
            )
