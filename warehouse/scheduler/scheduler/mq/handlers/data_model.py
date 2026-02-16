import asyncio

from aioprometheus.collectors import Counter, Histogram
from oso_core.instrumentation.common import MetricsLabeler
from oso_core.instrumentation.container import MetricsContainer
from oso_core.instrumentation.timing import async_time
from oso_dagster.resources.udm_engine_adapter import (
    UserDefinedModelEngineAdapterResource,
)
from osoprotobufs.data_model_pb2 import DataModelRunRequest
from queryrewriter.types import TableResolver
from scheduler.graphql_client.client import Client
from scheduler.graphql_client.fragments import DataModelsEdgesNode, DatasetCommon
from scheduler.graphql_client.get_data_models import (
    GetDataModelsDatasetsEdgesNodeTypeDefinitionDataModelDefinition,
)
from scheduler.graphql_client.input_types import DataModelColumnInput
from scheduler.mq.common import RunHandler
from scheduler.types import (
    HandlerResponse,
    Model,
    ModelSorter,
    RunContext,
    StepContext,
    SuccessResponse,
)
from scheduler.utils import OSOClientTableResolver, ctas_query, get_warehouse_user
from sqlglot import exp
from sqlmesh import EngineAdapter


def convert_model_to_scheduler_model(org_name: str, dataset_name: str, dataset_id: str):
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
            org_name=org_name,
            dataset_name=dataset_name,
        )

    return _convert


class DataModelRunRequestHandler(RunHandler[DataModelRunRequest]):
    topic = "data_model_run_requests"
    message_type = DataModelRunRequest
    schema_file_name = "data-model.proto"

    def initialize(self, metrics: MetricsContainer):
        metrics.initialize_histogram(
            Histogram(
                "data_model_selected_models_count",
                "Total number of data models in the run request",
            ),
        )
        metrics.initialize_counter(
            Counter(
                "data_model_response_total",
                "Total number of data model run request responses processed",
            ),
        )

        metrics.initialize_histogram(
            Histogram(
                "data_model_total_evaluation_duration_ms",
                "Duration of all the selected data model runs execution in milliseconds",
            )
        )

        metrics.initialize_histogram(
            Histogram(
                "data_model_individual_model_evaluation_duration_ms",
                "Duration of individual data model execution in milliseconds",
            )
        )

        return super().initialize(metrics)

    async def handle_run_message(
        self,
        context: RunContext,
        message: DataModelRunRequest,
        udm_engine_adapter: UserDefinedModelEngineAdapterResource,
        oso_client: Client,
        metrics: MetricsContainer,
    ) -> HandlerResponse:
        # Process the DataModelRunRequest message

        context.log.info(f"Handling DataModelRunRequest with ID: {context.run_id}")

        # Pull the model using the OSO client
        dataset_and_models = await oso_client.get_data_models(message.dataset_id)

        dataset = dataset_and_models.datasets.edges[0]

        # Get the selected models from the DataModelRunRequest
        selected_model_release_ids = message.model_release_ids

        labeler = MetricsLabeler(
            {
                "org_id": context.organization.id,
                "trigger_type": context.trigger_type,
                "dataset_id": message.dataset_id,
            }
        )

        # If no specific models are provided, run all models in the dataset
        data_model_def = dataset.node.type_definition
        dataset_name = dataset.node.name
        org_name = dataset.node.organization.name

        user = get_warehouse_user("rw", context.organization.id, org_name)

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

        metrics.histogram("data_model_selected_models_count").observe(
            labeler.get_labels(),
            len(selected_models),
        )

        # Remove models with no latest release
        models_with_release = [
            model for model in selected_models if model.latest_release is not None
        ]

        # Convert models into the scheduler's Model Type so we can run the evaluation
        converted_models: list[Model] = list(
            map(
                convert_model_to_scheduler_model(
                    org_name=org_name,
                    dataset_name=dataset_name,
                    dataset_id=message.dataset_id,
                ),
                models_with_release,
            )
        )

        context.log.info(
            f"Selected {len(selected_models)} models to run for dataset {message.dataset_id}"
        )

        if len(converted_models) == 0:
            context.log.info("No models to run, skipping evaluation.")
            return SuccessResponse(
                message=f"No models to run for DataModelRunRequest with ID: {context.run_id}"
            )

        async with async_time(
            metrics.histogram("data_model_total_evaluation_duration_ms"), labeler
        ):
            context.log.info("Starting evaluation of selected data models")
            try:
                await self.evaluate_models(
                    context=context,
                    dataset=dataset.node,
                    udm_engine_adapter=udm_engine_adapter,
                    oso_client=oso_client,
                    user=user,
                    converted_models=converted_models,
                    labeler=labeler,
                    metrics=metrics,
                )
            except Exception as e:
                context.log.error(f"Error during dataset evaluation: {e}")
                raise e

        return SuccessResponse(
            message=f"Processed DataModelRunRequest with ID: {context.run_id}"
        )

    async def evaluate_models(
        self,
        *,
        context: RunContext,
        dataset: DatasetCommon,
        udm_engine_adapter: UserDefinedModelEngineAdapterResource,
        oso_client: Client,
        user: str,
        converted_models: list[Model],
        metrics: MetricsContainer,
        labeler: MetricsLabeler,
    ) -> None:
        """Evaluate the provided models using the UDM engine adapter."""
        oso_table_resolver = OSOClientTableResolver(oso_client=oso_client)

        # Resolve all of the previously materialized models so we can drop old
        # tables opportunistically. We will need to completely change the
        # strategy for INCREMENTAL models in the future but this will satisfy
        # versioning in the future for FULL models.
        context.internal_log.debug(
            "Resolving previously materialized warehouse tables..."
        )

        previous_warehouse_tables = await oso_table_resolver.resolve_tables(
            {model.user_fqn(): model.user_table() for model in converted_models},
            metadata={
                "resolutionType": "data_model_run_previous_warehouse_tables_lookup",
                "runId": context.run_id,
                "orgName": context.organization.name,
                "datasetName": dataset.name,
            },
        )

        table_resolvers: list[TableResolver] = [oso_table_resolver]

        context.internal_log.debug("Opening connection to UDM engine adapter")
        async with udm_engine_adapter.get_adapter(user=user) as adapter:
            context.internal_log.info("Determining model evaluation order...")
            sorter = ModelSorter(converted_models)
            async for model in sorter.ordered_iter():
                context.internal_log.info(f"Evaluating model: {model.name}")
                async with context.step_context(
                    name=f"evaluate_model_{model.name}",
                    display_name=f"Evaluate Model {model.name}",
                ) as step_context:
                    async with async_time(
                        metrics.histogram(
                            "data_model_individual_model_evaluation_duration_ms"
                        ),
                        labeler,
                    ):
                        previous_warehouse_table = previous_warehouse_tables.get(
                            model.user_fqn()
                        )
                        if previous_warehouse_table:
                            context.internal_log.debug(
                                f"Found previous warehouse table for model {model.name}: {previous_warehouse_table}"
                            )
                        try:
                            await self.evaluate_single_model(
                                model=model,
                                step_context=step_context,
                                adapter=adapter,
                                table_resolvers=table_resolvers,
                                metrics=metrics,
                                labeler=labeler,
                                previous_warehouse_table=previous_warehouse_table,
                            )
                        except Exception as e:
                            step_context.log.error(
                                f"Error during model evaluation: {e}"
                            )
                            raise e

    async def evaluate_single_model(
        self,
        *,
        step_context: StepContext,
        model: Model,
        adapter: EngineAdapter,
        table_resolvers: list[TableResolver],
        metrics: MetricsContainer,
        labeler: MetricsLabeler,
        previous_warehouse_table: exp.Table | None = None,
    ):
        step_context.log.info(f"Starting evaluation for model {model.name}")

        assert model.language.lower() == "sql", (
            "Only SQL models are supported for evaluation at this time."
        )

        # If we use the run id for the table ref we will accidentally write to
        # the same place for all tables in a dataset. We need to use the step id
        # to ensure uniqueness per model.
        table_ref = model.warehouse_table_ref(destination_suffix=step_context.step_id)

        target_table = step_context.generate_destination_table_exp(table_ref)

        step_context.internal_log.info("Writing to target table: %s", target_table)
        step_context.log.info("Writing model results to the warehouse.")
        adapter.create_schema(
            f"{target_table.catalog}.{target_table.db}",
            ignore_if_exists=True,
        )

        resolved_query = await model.resolve_query(
            table_resolvers=table_resolvers,
            metadata={
                "resolutionType": "data_model_run",
                "runId": step_context.run.id,
                "stepId": step_context.step_id,
                "orgName": step_context.run.organization.name,
                "datasetName": model.dataset_name,
            },
        )

        # Add human readable comments for admins to more easily debug queries
        resolved_query_comments = [
            "Query Type: Data Model",
            f"Organization: {step_context.run.organization.name}",
            f"Dataset: {model.dataset_name}",
            f"Model: {model.name}",
            f"Run ID: {step_context.run.id}",
            f"Step ID: {step_context.step_id}",
        ]
        resolved_query.add_comments(resolved_query_comments, prepend=True)

        step_context.log.info(
            f"Executing query for model {model.name} on the warehouse"
        )

        await asyncio.to_thread(
            self.make_synchronous_trino_requests,
            adapter,
            resolved_query,
            target_table,
        )

        step_context.log.info(
            f"Model {model.name} successfully written to the warehouse"
        )

        columns = adapter.columns(table_name=target_table)

        # Create the schema for the materialization
        schema: list[DataModelColumnInput] = []
        columns_logging: list[str] = []
        for name, data_type in columns.items():
            data_type_name = data_type.sql(dialect=adapter.dialect)
            columns_logging.append(f"Column: {name}, Type: {data_type_name}")
            schema.append(
                DataModelColumnInput(
                    name=name,
                    type=data_type_name,
                )
            )
        step_context.log.info(
            f"Resolved columns for model {model.name}: {columns_logging}"
        )

        step_context.log.info(
            f"Creating materialization record for run: {step_context.run.id} and step: {step_context.step_id}"
        )
        try:
            await step_context.create_materialization(
                table_id=model.table_id,
                warehouse_fqn=f"{target_table.catalog}.{target_table.db}.{target_table.name}",
                schema=schema,
            )
        except Exception as e:
            step_context.log.error(f"Error creating materialization: {e}")
            raise e

        # If we've reached this point everything has been successfully
        # materialized. We can now drop the previous table if it exists.
        # We do this as a best-effort attempt and log a warning if it fails.
        if previous_warehouse_table:
            try:
                adapter.drop_table(
                    table_name=previous_warehouse_table,
                    exists=True,
                )
            except Exception as e:
                # This is a system level log not one for the users
                step_context.internal_log.warning(
                    f"Failed to drop previous warehouse table "
                    f"{previous_warehouse_table}: {e}"
                )

    def make_synchronous_trino_requests(
        self, adapter: EngineAdapter, resolved_query: exp.Query, target_table: exp.Table
    ):
        """Queries to the engine adapter are made using the synchronous client.
        This method will be wrapped with asyncio.to_thread to ensure we don't
        block the main event loop."""
        create_query = ctas_query(resolved_query)

        adapter.ctas(
            table_name=target_table,
            query_or_df=create_query,
            exists=True,
        )
        adapter.replace_query(
            table_name=target_table,
            query_or_df=resolved_query,
        )
