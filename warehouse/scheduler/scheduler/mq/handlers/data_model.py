import uuid

import structlog
from osoprotobufs.data_model_pb2 import DataModelRunRequest
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.enums import RunStatus, StepStatus
from scheduler.graphql_client.get_data_models import (
    GetDataModelsDatasetsEdgesNodeTypeDefinitionDataModelDefinition,
)
from scheduler.graphql_client.input_types import DataModelColumnInput
from scheduler.types import MessageHandler
from scheduler.utils import convert_uuid_bytes_to_str

logger = structlog.getLogger(__name__)


class DataModelRunRequestHandler(MessageHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest
    schema_file_name = "data-model.proto"

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

        run_id_str = convert_uuid_bytes_to_str(message.run_id)

        print(f"Starting run with ID: {run_id_str}")

        # Fake
        await oso_client.start_run(run_id=run_id_str)

        # Start a step
        step = await oso_client.start_step(
            run_id=run_id_str,
            name=f"fake_step_{str(uuid.uuid4())}",
            display_name="Fake step",
        )
        step_id = step.start_step.step.id

        # Add a materialization
        schema: list[DataModelColumnInput] = [
            DataModelColumnInput(name="col1", type="STRING"),
        ]
        await oso_client.create_materialization(
            step_id=step_id,
            table_id="fake_table_id",
            warehouse_fqn="fake.warehouse.fqn",
            schema=schema,
        )

        # Finish the step
        await oso_client.finish_step(
            step_id=step_id,
            status=StepStatus.SUCCESS,
            logs_url="http://example.com/logs",
        )

        # Finish the run
        await oso_client.finish_run(
            run_id=run_id_str,
            status=RunStatus.SUCCESS,
            logs_url="http://example.com/run_logs",
        )

        # For each selected model, run the evaluation

        # Turn the model into the scheduler's Model Type so we can run the evaluation
        # TODO Run each selected model in a DAG
