import structlog
from oso_dagster.resources.udm_engine_adapter import (
    UserDefinedModelEngineAdapterResource,
)
from osoprotobufs.data_model_pb2 import DataModelRunRequest
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.fragments import DataModelsEdgesNode
from scheduler.graphql_client.get_data_models import (
    GetDataModelsDatasetsEdgesNodeTypeDefinitionDataModelDefinition,
)
from scheduler.graphql_client.input_types import DataModelColumnInput
from scheduler.mq.common import RunHandler
from scheduler.types import HandlerResponse, Model, RunContext, SuccessResponse

logger = structlog.getLogger(__name__)


def convert_model_to_scheduler_model(dataset_id: str):
    """Convert a data model from the UDM client to the scheduler's Model type."""

    def _convert(raw: DataModelsEdgesNode) -> "Model":
        # Placeholder conversion logic

        latest_release = raw.latest_release
        assert latest_release is not None, "Model must have a latest release"

        revision = latest_release.revision

        return Model(
            id=raw.id,
            org_id=raw.org_id,
            dataset_id=dataset_id,
            name=revision.name,
            code=revision.code,
            language=revision.language,
        )

    return _convert


class DataModelRunRequestHandler(RunHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest
    schema_file_name = "data-model.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        message: DataModelRunRequest,
        udm_engine_adapter: UserDefinedModelEngineAdapterResource,
        oso_client: Client,
    ) -> HandlerResponse:
        # Process the DataModelRunRequest message
        context.log.info(f"Handling DataModelRunRequest with ID: {message.run_id}")

        # Pull the model using the OSO client
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

        # Remove models with no latest release
        models_with_release = [
            model for model in selected_models if model.latest_release is not None
        ]

        # Convert models into the scheduler's Model Type so we can run the evaluation
        converted_models = list(
            map(
                convert_model_to_scheduler_model(dataset_id=message.dataset_id),
                models_with_release,
            )
        )

        context.log.info(
            f"Selected {len(selected_models)} models to run for dataset {message.dataset_id}"
        )

        if len(converted_models) == 0:
            context.log.info("No models to run, skipping evaluation.")
            return SuccessResponse(
                message=f"No models to run for DataModelRunRequest with ID: {message.run_id}"
            )

        async with udm_engine_adapter.get_adapter() as adapter:
            for model in converted_models:
                async with context.step_context(
                    name=f"evaluate_model_{model.name}",
                    display_name=f"Evaluate Model {model.name}",
                ) as step_context:
                    step_context.log.info(f"Starting evaluation for model {model.name}")

                    adapter.ctas(
                        table_name=model.backend_table(),
                        query_or_df=model.ctas_query(),
                        exists=True,
                    )

                    adapter.insert_append(
                        table_name=model.backend_table(),
                        query_or_df=model.query,
                    )

                    # Add a materialization
                    schema: list[DataModelColumnInput] = [
                        DataModelColumnInput(name="col1", type="STRING"),
                    ]
                    await step_context.create_materialization(
                        table_id="fake_table_id",
                        warehouse_fqn="fake.warehouse.fqn",
                        schema=schema,
                    )
        return SuccessResponse(
            message=f"Processed DataModelRunRequest with ID: {message.run_id}"
        )
