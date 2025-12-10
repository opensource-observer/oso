from osoprotobufs.data_model_pb2 import DataModelRunRequest
from scheduler.evaluator import UserDefinedModelEvaluator, UserDefinedModelStateClient
from scheduler.types import AsyncMessageQueueHandler


class DataModelRunRequestHandler(AsyncMessageQueueHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest

    async def handle_message(
        self,
        *,
        message: DataModelRunRequest,
        evaluator: UserDefinedModelEvaluator,
        udm_client: UserDefinedModelStateClient,
        **kwargs,
    ) -> None:
        # Process the DataModelRunRequest message
        print(f"Handling DataModelRunRequest with ID: {message.run_id}")

        # Pull the model using the UDM client
