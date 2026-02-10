import asyncio

from dlt import pipeline
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from pydantic import BaseModel, ConfigDict, ValidationError
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


class _RESTAPIConfigWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: RESTAPIConfig


class RestIngestionHandler(IngestionHandler):
    """Handler for REST API data ingestion using DLT."""

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
        """Execute REST API data ingestion.

        Args:
            context: The run context
            step_context: The step context for logging and materialization
            config: The REST API configuration dictionary
            dataset_id: The dataset ID
            org_id: The organization ID
            dlt_destination: DLT destination resource
            common_settings: Common settings

        Returns:
            HandlerResponse indicating success or failure
        """

        try:
            try:
                rest_api_config: RESTAPIConfig = _RESTAPIConfigWrapper.model_validate(
                    {"config": config}
                ).config
            except ValidationError as e:
                step_context.log.error(
                    "Invalid REST API config", extra={"errors": e.errors()}
                )
                return FailedResponse(message="Invalid REST API config")

            step_context.log.info(
                "Creating REST API resources",
                extra={
                    "dataset_id": dataset_id,
                    "num_endpoints": len(rest_api_config.get("resources", [])),
                },
            )

            dlt_resources = rest_api_resources(rest_api_config)

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

                load_info = await asyncio.to_thread(p.run, dlt_resources)

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
