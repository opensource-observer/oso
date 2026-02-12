import asyncio
import typing as t

import dlt
import structlog
from dlt.sources.credentials import FileSystemCredentials
from dlt.sources.filesystem import readers
from osoprotobufs.static_model_pb2 import StaticModelRunRequest
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.graphql_client.client import Client
from scheduler.mq.common import RunHandler
from scheduler.types import (
    FailedResponse,
    HandlerResponse,
    RunContext,
    SuccessResponse,
    TableReference,
)
from scheduler.utils import dlt_to_oso_schema

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings

logger = structlog.getLogger(__name__)


class StaticModelRunRequestHandler(RunHandler[StaticModelRunRequest]):
    topic = "static_model_run_requests"
    message_type = StaticModelRunRequest
    schema_file_name = "static-model.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        message: StaticModelRunRequest,
        common_settings: "CommonSettings",
        dlt_destination: DLTDestinationResource,
        upload_filesystem_credentials: FileSystemCredentials | None,
        oso_client: Client,
    ) -> HandlerResponse:
        num_models = len(message.model_ids)

        context.log.info(
            "Received StaticModelRunRequest",
            extra={
                "dataset_id": message.dataset_id,
                "num_models": num_models,
            },
        )

        if not upload_filesystem_credentials:
            raise ValueError("Upload filesystem credentials are not provided.")

        # Get the static model dataset from the server
        try:
            dataset_and_models = await oso_client.get_static_models(message.dataset_id)
        except Exception as e:
            context.log.error(
                "Failed to fetch static model dataset and models",
                extra={
                    "dataset_id": message.dataset_id,
                    "error": str(e),
                },
            )
            return FailedResponse(
                exception=e,
                message=f"Failed to fetch static model dataset and models for dataset ID: {message.dataset_id}",
            )

        edges = dataset_and_models.datasets.edges
        if not edges or len(edges) != 1:
            context.log.error(
                "Dataset not found", extra={"dataset_id": message.dataset_id}
            )
            return FailedResponse(message="Dataset not found")

        dataset = dataset_and_models.datasets.edges[0]

        org_id = dataset.node.organization.id

        placeholder_table_ref = TableReference(
            org_id=org_id,
            dataset_id=message.dataset_id,
            table_id="placeholder_table",
        )

        placeholder_destination_table = context.generate_destination_table_exp(
            placeholder_table_ref
        )

        catalog_name = placeholder_destination_table.catalog
        schema_name = placeholder_destination_table.db

        context.log.info(
            "Starting processing of static models",
            extra={
                "dataset_id": message.dataset_id,
                "num_models": num_models,
            },
        )

        async with dlt_destination.get_destination(
            dataset_schema=schema_name,
        ) as dlt_destination_instance:
            for model_id in message.model_ids:
                async with context.step_context(
                    name=f"static_model_{model_id}",
                    display_name=f"Static Model {model_id}",
                ) as step_context:
                    table_name = model_id.replace("-", "_")
                    step_context.log.info(
                        "Processing static model",
                        extra={
                            "model_id": model_id,
                            "dataset_id": message.dataset_id,
                        },
                    )
                    source_csvs = readers(
                        bucket_url=common_settings.upload_filesystem_bucket_url,
                        file_glob=f"{message.dataset_id}/{model_id}",
                        credentials=upload_filesystem_credentials,
                    ).read_csv()

                    source_csvs.apply_hints(write_disposition="replace")

                    pipeline = dlt.pipeline(
                        pipeline_name=f"static_model_{model_id}",
                        dataset_name=schema_name,
                        destination=dlt_destination_instance,
                        pipelines_dir=common_settings.local_working_dir,
                    )

                    step_context.log.info(
                        "Running dlt pipeline",
                        extra={
                            "pipeline_name": f"static_model_{model_id}",
                            "dataset_schema": schema_name,
                        },
                    )

                    await asyncio.to_thread(
                        pipeline.run, source_csvs.with_name(table_name)
                    )

                    step_context.log.info(
                        "Static model processing completed successfully",
                        extra={
                            "model_id": model_id,
                            "dataset_id": message.dataset_id,
                        },
                    )

                    tables = pipeline.default_schema.data_tables()

                    if len(tables) == 0:
                        step_context.log.error(
                            "No tables found after processing static model",
                            extra={
                                "model_id": model_id,
                                "dataset_id": message.dataset_id,
                            },
                        )
                        return FailedResponse(
                            message=f"No tables found after processing static model {model_id}"
                        )

                    table = tables[0]

                    warehouse_fqn = f"{catalog_name}.{schema_name}.{table.get('name')}"

                    await step_context.create_materialization(
                        table_id=f"static_model_{model_id}",
                        warehouse_fqn=warehouse_fqn,
                        schema=dlt_to_oso_schema(table.get("columns")),
                    )

                    step_context.log.info(
                        "Created materialization",
                        extra={
                            "model_id": model_id,
                            "warehouse_fqn": warehouse_fqn,
                        },
                    )

        context.log.info(
            "Static model processing completed successfully",
            extra={
                "dataset_id": message.dataset_id,
                "num_models": num_models,
            },
        )

        return SuccessResponse(
            message=f"Processed StaticModelRunRequest with ID: {message.run_id}"
        )
