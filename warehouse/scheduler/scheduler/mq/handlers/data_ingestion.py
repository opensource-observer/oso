import asyncio

from dlt import pipeline
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from osoprotobufs.data_ingestion_pb2 import DataIngestionRunRequest
from pydantic import BaseModel, ConfigDict, ValidationError
from scheduler.config import CommonSettings
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.get_data_ingestion_config import (
    GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestion,
)
from scheduler.mq.common import RunHandler
from scheduler.types import FailedResponse, HandlerResponse, RunContext, SuccessResponse
from scheduler.utils import convert_uuid_bytes_to_str


class _RESTAPIConfigWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: RESTAPIConfig


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
        config_id_bytes = bytes(message.config_id)
        dataset_id = message.dataset_id

        config_id = convert_uuid_bytes_to_str(config_id_bytes)

        context.log.info(
            "Received DataIngestionRunRequest",
            dataset_id=dataset_id,
            config_id=config_id,
        )

        try:
            config_response = await oso_client.get_data_ingestion_config(
                dataset_id=dataset_id,
                config_id=config_id,
            )
        except Exception as e:
            context.log.error(
                "Failed to fetch config", config_id=config_id, error=str(e)
            )
            return FailedResponse(message=f"Config fetch failed: {e}")

        edges = config_response.datasets.edges
        if not edges or not edges[0].node.type_definition:
            context.log.error("Config not found", config_id=config_id)
            return FailedResponse(message="Config not found")

        type_def = edges[0].node.type_definition

        if not isinstance(
            type_def,
            GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestion,
        ):
            context.log.error(
                "Dataset is not a DataIngestion type",
                type=type_def.typename__,
            )
            return FailedResponse(message=f"Wrong dataset type: {type_def.typename__}")

        if not type_def.configs.edges:
            context.log.error("No configs found")
            return FailedResponse(message="Config not found")

        config = type_def.configs.edges[0].node

        if config.factory_type != "REST":
            context.log.error(
                "Unsupported factory type",
                factory_type=config.factory_type,
            )
            return FailedResponse(message=f"Unsupported type: {config.factory_type}")

        context.log.info(
            "Config validated",
            config_id=config_id,
            factory_type=config.factory_type,
        )

        async with context.step_context(
            name="execute_data_ingestion_pipeline",
            display_name="Execute Data Ingestion Pipeline",
        ) as step_context:
            try:
                try:
                    rest_api_config: RESTAPIConfig = (
                        _RESTAPIConfigWrapper.model_validate(
                            {"config": config.config}
                        ).config
                    )
                except ValidationError as e:
                    step_context.log.error("Invalid REST API config", errors=e.errors())
                    return FailedResponse(message="Invalid REST API config")

                step_context.log.info(
                    "Creating REST API resources",
                    config_id=config_id,
                    num_endpoints=len(rest_api_config.get("resources", [])),
                )

                resources = rest_api_resources(rest_api_config)

                dataset_schema = f"ingest_{dataset_id.replace('-', '_')}"
                pipeline_name = f"data_ingestion_{dataset_id}_{config_id}"[:50]
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
                        pipeline_name=pipeline_name,
                        dataset_schema=dataset_schema,
                    )

                    load_info = await asyncio.to_thread(p.run, resources)

                step_context.log.info(
                    "Data ingestion completed successfully",
                    pipeline_name=pipeline_name,
                    loaded_packages=len(load_info.loads_ids) if load_info else 0,
                )

            except Exception as e:
                step_context.log.error(
                    "Data ingestion failed",
                    error=str(e),
                    exc_info=True,
                )
                return FailedResponse(message=f"Data ingestion failed: {e}")

        return SuccessResponse(message="Data ingestion completed successfully")
