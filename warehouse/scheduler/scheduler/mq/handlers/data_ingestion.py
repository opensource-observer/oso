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
from scheduler.utils import dlt_to_oso_schema


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
        org_id = node.org_id

        if not isinstance(
            type_def,
            GetDataIngestionConfigDatasetsEdgesNodeTypeDefinitionDataIngestion,
        ):
            context.log.error(
                "Dataset is not a DataIngestion type",
                extra={"type": type_def.typename__},
            )
            return FailedResponse(message=f"Wrong dataset type: {type_def.typename__}")

        config = type_def

        if config.factory_type != "REST":
            context.log.error(
                "Unsupported factory type",
                extra={"factory_type": config.factory_type},
            )
            return FailedResponse(message=f"Unsupported type: {config.factory_type}")

        context.log.info(
            "Config validated",
            extra={
                "dataset_id": dataset_id,
                "config_id": config.id,
                "factory_type": config.factory_type,
            },
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
                    step_context.log.error(
                        "Invalid REST API config", extra={"errors": e.errors()}
                    )
                    return FailedResponse(message="Invalid REST API config")

                step_context.log.info(
                    "Creating REST API resources",
                    extra={
                        "dataset_id": dataset_id,
                        "config_id": config.id,
                        "num_endpoints": len(rest_api_config.get("resources", [])),
                    },
                )

                resources = rest_api_resources(rest_api_config)

                dataset_schema = f"org_{org_id}__{dataset_id}".replace("-", "")
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

                    load_info = await asyncio.to_thread(p.run, resources)

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
                    "Data ingestion failed",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                return FailedResponse(message=f"Data ingestion failed: {e}")

        return SuccessResponse(message="Data ingestion completed successfully")
