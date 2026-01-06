import typing as t

import dlt
import structlog
from dlt.sources.credentials import FileSystemCredentials
from dlt.sources.filesystem import readers
from osoprotobufs.static_model_pb2 import StaticModelRunRequest
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.mq.common import RunHandler
from scheduler.types import HandlerResponse, RunContext, SuccessResponse

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings

logger = structlog.getLogger(__name__)


class StaticModelRunRequestHandler(RunHandler[StaticModelRunRequest]):
    topic = "static_model_run_requests"
    message_type = StaticModelRunRequest
    schema_file_name = "static_model.proto"

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

        async with dlt_destination.get_destination(
            dataset_schema=f"static_model_{message.run_id}"
        ) as dlt_destination_instance:
            source_csvs = readers(
                bucket_url=common_settings.upload_filesystem_bucket_url,
                credentials=upload_filesystem_credentials,
                file_glob="{dataset_id}/*",
            ).read_csv()

            pipeline = dlt.pipeline(
                pipeline_name=f"static_model_{message.run_id}",
                destination=dlt_destination_instance,
            )

            pipeline.run(source_csvs.with_name("{destination_table_name}"))

        return SuccessResponse(
            message=f"Processed StaticModelRunRequest with ID: {message.run_id}"
        )
