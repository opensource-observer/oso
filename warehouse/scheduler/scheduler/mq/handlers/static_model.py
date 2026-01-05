
import structlog
from osoprotobufs.static_model_pb2 import StaticModelRunRequest
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.mq.common import RunHandler
from scheduler.types import HandlerResponse, RunContext, SuccessResponse

logger = structlog.getLogger(__name__)


class StaticModelRunRequestHandler(RunHandler[StaticModelRunRequest]):
    topic = "static_model_run_requests"
    message_type = StaticModelRunRequest
    schema_file_name = "static_model.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        message: StaticModelRunRequest,
        dlt_destination: DLTDestinationResource,
    ) -> HandlerResponse:
        # Process the StaticModelRunRequest message
        context.log.info(f"Handling StaticModelRunRequest with ID: {message.run_id}")

        return SuccessResponse(
            message=f"Processed StaticModelRunRequest with ID: {message.run_id}"
        )
