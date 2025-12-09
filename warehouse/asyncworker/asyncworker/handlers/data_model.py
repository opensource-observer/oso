from asyncworker.types import AsyncMessageQueueHandler
from oso_core.resources import ResourcesContext
from osoprotobufs.data_model_pb2 import DataModelRunRequest
from scheduler.evaluator import UserDefinedModelEvaluator, UserDefinedModelStateClient


class DataModelRunRequestHandler(AsyncMessageQueueHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest

    async def handle_message(
        self,
        *,
        resources: ResourcesContext,
        message: DataModelRunRequest,
        evaluator: UserDefinedModelEvaluator,
        udm_client: UserDefinedModelStateClient,
        **kwargs,
    ) -> None:
        # Process the DataModelRunRequest message
        print(f"Handling DataModelRunRequest with ID: {message.run_id}")
