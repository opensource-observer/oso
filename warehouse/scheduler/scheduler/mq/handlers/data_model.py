import structlog
from osoprotobufs.data_model_pb2 import DataModelRunRequest
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.get_data_models import (
    GetDataModelsDatasetsEdgesNodeTypeDefinitionDataModelDefinition,
)
from scheduler.types import MessageHandler

logger = structlog.getLogger(__name__)


class DataModelRunRequestHandler(MessageHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest

    async def handle_message(
        self,
        *,
        message: DataModelRunRequest,
        oso_client: Client,
        **kwargs,
    ) -> None:
        # Process the DataModelRunRequest message
        print(f"Handling DataModelRunRequest with ID: {message.run_id}")

        # Pull the model using the UDM client
        dataset_and_models = await oso_client.get_data_models(message.dataset_id)

        dataset = dataset_and_models.datasets.edges[0]

        # Get the selected models from the DataModelRunRequest
        selected_model_release_ids = message.model_release_ids

        # If no specific models are provided, run all models in the dataset
        data_model_def = dataset.node.type_definition

        assert isinstance(
            data_model_def,
            GetDataModelsDatasetsEdgesNodeTypeDefinitionDataModelDefinition,
        )

        if not selected_model_release_ids:
            selected_models = [edge.node for edge in data_model_def.data_models.edges]
        else:
            selected_models = [
                edge.node
                for edge in data_model_def.data_models.edges
                if edge.node.id in selected_model_release_ids
            ]

        print(
            f"Selected {len(selected_models)} models to run for dataset {message.dataset_id}"
        )

        # Turn the model into the scheduler's Model Type so we can run the evaluation
        # TODO Run each selected model in a DAG
