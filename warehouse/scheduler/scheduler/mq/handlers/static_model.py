import asyncio
import typing as t

import dlt
import structlog
from dlt.sources.credentials import FileSystemCredentials
from dlt.sources.filesystem import readers
from osoprotobufs.static_model_pb2 import StaticModelRunRequest
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.mq.common import RunHandler
from scheduler.types import FailedResponse, HandlerResponse, RunContext, SuccessResponse
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
    ) -> HandlerResponse:
        # Process the StaticModelRunRequest message
        context.log.info(f"Handling StaticModelRunRequest with ID: {message.run_id}")

        if not upload_filesystem_credentials:
            raise ValueError("Upload filesystem credentials are not provided.")

        schema_name = message.dataset_id.replace("-", "_")

        async with dlt_destination.get_destination(
            dataset_schema=schema_name,
        ) as dlt_destination_instance:
            for model_id in message.model_ids:
                async with context.step_context(
                    name=f"static_model_{model_id}",
                    display_name=f"Static Model {model_id}",
                ) as step_context:
                    table_name = model_id.replace("-", "_")
                    context.log.info(
                        f"Processing static model {model_id} for dataset {message.dataset_id}"
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
                    )

                    await asyncio.to_thread(
                        pipeline.run, source_csvs.with_name(table_name)
                    )

                    context.log.info(
                        f"Completed processing static model {model_id} for dataset {message.dataset_id}"
                    )

                    tables = pipeline.default_schema.data_tables()

                    if len(tables) == 0:
                        return FailedResponse(
                            message=f"No tables found after processing static model {model_id}"
                        )

                    table = tables[0]

                    await step_context.create_materialization(
                        table_id=f"static_model_{model_id}",
                        warehouse_fqn=f"iceberg.{schema_name}.{table.get('name')}",
                        schema=dlt_to_oso_schema(table.get("columns")),
                    )

                    context.log.info(
                        f"Created materialization for static model {model_id}"
                    )

        return SuccessResponse(
            message=f"Processed StaticModelRunRequest with ID: {message.run_id}"
        )
