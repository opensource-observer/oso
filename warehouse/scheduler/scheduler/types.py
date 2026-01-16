import abc
import logging
import typing as t
from graphlib import TopologicalSorter

import structlog
from google.protobuf.json_format import Parse
from google.protobuf.message import Message
from oso_core.instrumentation import MetricsContainer
from oso_core.resources import ResourcesContext
from pydantic import BaseModel, Field
from queryrewriter.rewrite import rewrite_query
from queryrewriter.types import RewriteResponse, TableResolver
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.fragments import (
    DatasetCommon,
    OrganizationCommon,
    UserCommon,
)
from scheduler.graphql_client.input_types import DataModelColumnInput
from scheduler.graphql_client.update_run_metadata import UpdateRunMetadata
from sqlglot import exp, parse_one
from sqlglot.optimizer.qualify_columns import qualify_columns
from sqlglot.optimizer.scope import build_scope
from sqlmesh.core import dialect as sqlmesh_dialect

logger = structlog.getLogger(__name__)


class SchemaRetreiver(abc.ABC):
    """A way for us to load schemas for table dependencies. This is important
    for determing column types from queries. It's also useful to comparing
    models for breaking changes."""

    @abc.abstractmethod
    async def get_table_schema(self, table_name: str) -> dict[str, exp.DataType]:
        """Get the schema for a given table.

        Args:
            table_name: The name of the table.

        Returns:
            A dictionary mapping column names to their data types.
        """
        raise NotImplementedError("get_table_schema must be implemented by subclasses.")


class TableReference(BaseModel):
    """A reference to a user defined model."""

    org_id: str
    dataset_id: str
    table_id: str

    def __str__(self) -> str:
        return f"{self.org_id}.{self.dataset_id}.{self.table_id}"


class MaterializationStrategy(abc.ABC):
    """A strategy for materializing models using an engine adapter."""

    @abc.abstractmethod
    def destination_fqn(self, ref: TableReference) -> str:
        """Convert a TableReference to a fully qualified name in the engine adapter.

        Returns:
            The fully qualified name of the table.
        """
        raise NotImplementedError("destination_fqn must be implemented by subclasses.")


class ModelFQNResolver(TableResolver):
    """
    A table resolver that resolves model table references to their fully
    qualified names. For a USER_MODEL table references are resolved with the
    following logic:
    * {org_name}.{dataset_name}.{table_name}
        * No further resolution is done. This is an FQN already.
    * {dataset_name}.{table_name}
        * The org_name is assumed to be the current org.
    * {table_name}
        * The org_name is assumed to be the current org.
        * The dataset_name is assumed to be "default_dataset".
    """

    def __init__(self, org_name: str, dataset_name: str):
        self.org_name = org_name
        self.dataset_name = dataset_name

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
        *,
        metadata: dict | None = None,
    ) -> dict[str, exp.Table]:
        resolved: dict[str, exp.Table] = {}
        for table_id, table in tables.items():
            if table.catalog and table.db and table.name:
                # Fully qualified name already
                resolved[table_id] = table
            elif table.db and table.name:
                # Missing catalog/org
                fqn = f"{self.org_name}.{table.db}.{table.name}"
                resolved[table_id] = exp.to_table(fqn)
            elif table.name:
                # Missing catalog/org and db/dataset
                fqn = f"{self.org_name}.{self.dataset_name}.{table.name}"
                resolved[table_id] = exp.to_table(fqn)
            else:
                raise ValueError(f"Table {table_id} has no name.")
        return resolved


class Model(BaseModel):
    """User defined model

    Initially a lot of this was forked from sqlmesh's model class.
    """

    org_id: str
    org_name: str
    id: str
    name: str
    dataset_id: str
    dataset_name: str
    language: str
    code: str
    dialect: str = "trino"

    def __init__(self, *args: t.Any, **data: t.Any):
        super().__init__(*args, **data)
        self._parsed_query = None
        self._resolved_intermediate_query: RewriteResponse | None = None

    @property
    def query(self) -> exp.Query:
        if self._parsed_query is None:
            parsed = parse_one(self.code)
            assert isinstance(parsed, exp.Query)
            self._parsed_query = t.cast(exp.Query, parsed)
        return self._parsed_query

    async def _resolve_intermediate_query(self) -> RewriteResponse:
        """
        We want to resolve model queries in two steps. The intermediate
        resolver step will ensure that _all_ table references are fully
        qualified. This allows us to then determine internal dependency graphs
        within a group of models.
        """

        if self._resolved_intermediate_query is None:
            logger.info(f"Rewriting model {self.name} for intermediate resolution.")

            resolver = ModelFQNResolver(self.org_name, self.dataset_name)
            rewrite_response = await rewrite_query(
                self.query.sql(self.dialect),
                [resolver],
                input_dialect=self.dialect,
                output_dialect=self.dialect,
            )
            self._resolved_intermediate_query = rewrite_response

        return self._resolved_intermediate_query

    async def dependencies(self) -> list[str]:
        """Get the table references for the model's dependencies."""
        rewrite_response = await self._resolve_intermediate_query()
        return list(rewrite_response.tables.values())

    async def dataset_internal_dependencies(self) -> list[str]:
        """List of dependencies in the same dataset as this model."""
        rewrite_response = await self._resolve_intermediate_query()
        internal_dependencies: list[str] = []
        for table_fqn in rewrite_response.tables.values():
            table = exp.to_table(table_fqn)
            if table.db == self.dataset_name:
                internal_dependencies.append(table_fqn)
        return internal_dependencies

    async def org_internal_dependencies(self) -> list[str]:
        """List of dependencies in the same org as this model."""
        rewrite_response = await self._resolve_intermediate_query()
        internal_dependencies: list[str] = []
        for table_fqn in rewrite_response.tables.values():
            table = exp.to_table(table_fqn)
            if table.catalog == self.org_name:
                internal_dependencies.append(table_fqn)
        return internal_dependencies

    async def resolve_query(
        self,
        table_resolvers: list[TableResolver],
    ) -> exp.Query:
        """Users write queries to virtual names for all of the tables. These
        names must be resolved. This resolver returns a ResolvedSQLModel which
        has the query with all of the virtual names replaced with the actual
        table names in the data warehouse and other important metadata to use
        for ordering materializations.
        """
        logger.info(f"Rewriting model {self.name} with table resolvers.")
        rewrite_response = await rewrite_query(
            self.query.sql(self.dialect),
            table_resolvers,
            input_dialect=self.dialect,
            output_dialect=self.dialect,
        )
        logger.info(
            f"Finished rewriting model {self.name} as {rewrite_response.rewritten_query}."
        )
        parsed_query = parse_one(rewrite_response.rewritten_query)
        assert isinstance(parsed_query, exp.Query)
        return parsed_query

    async def calculate_columns(
        self, default_catalog: str, schema_retriever: SchemaRetreiver
    ) -> dict[str, exp.DataType]:
        """Calculate the columns of the model based on the query."""
        # Load all of the schemas for the dependencies in the query
        dependencies = sqlmesh_dialect.find_tables(
            self.query, default_catalog=default_catalog
        )

        schemas = {}
        for dependency in dependencies:
            schemas[dependency] = await schema_retriever.get_table_schema(dependency)

        # Resolve the columns in the query
        query_with_qualified_columns = qualify_columns(self.query, schemas)

        scope = build_scope(query_with_qualified_columns)

        if not scope:
            raise ValueError("Could not build scope for query.")

        columns = t.cast(list[exp.Column], scope.columns)

        column_names = set()

        for c in columns:
            name = c.alias_or_name
            if name in column_names:
                raise ValueError(f"Duplicate column name '{name}' found in query.")

            column_names.add(name)

        return {}

    def ctas_query(self, **render_kwarg: t.Any) -> exp.Query:
        """Return a dummy query to do a CTAS.

        If a model's column types are unknown, the only way to create the table is to
        run the fully expanded query. This can be expensive so we add a WHERE FALSE to all
        SELECTS and hopefully the optimizer is smart enough to not do anything.

        Args:
            render_kwarg: Additional kwargs to pass to the renderer.
        Return:
            The mocked out ctas query.
        """
        query = self.query.limit(0)

        for select_or_set_op in query.find_all(exp.Select, exp.SetOperation):
            if isinstance(select_or_set_op, exp.Select) and select_or_set_op.args.get(
                "from"
            ):
                select_or_set_op.where(exp.false(), copy=False)

        return query

    def format_uuid_id_str(self, id_str: str) -> str:
        """Removes dashes from a UUID string to make it safe for table/dataset names."""
        return id_str.replace("-", "")

    def backend_table_name(self):
        """Returns the _actual_ table name for this model.

        Table names are of the form: tbl_{model_id}.
        """
        return f"tbl_{self.format_uuid_id_str(self.id)}"

    def backend_db_name(self):
        """Returns the _actual_ dataset name for this model.

        Dataset names are of the form: ds_{dataset_id}.
        """
        return f"ds_{self.format_uuid_id_str(self.dataset_id)}"

    def backend_table(self) -> exp.Table:
        """Returns the fully qualified table for this model."""

        return exp.to_table(f"{self.backend_db_name()}.{self.backend_table_name()}")

    def __str__(self) -> str:
        return f"{self.org_name}.{self.dataset_name}.{self.name}"

    def table_reference(self) -> TableReference:
        """Get the table reference for the model itself."""
        return TableReference(
            org_id=self.org_id,
            dataset_id=self.dataset_id,
            table_id=f"data_model_{self.id}",
        )


class ModelSorter:
    def __init__(self, models: list[Model]) -> None:
        self._models = models

    async def ordered_iter(self) -> t.AsyncGenerator[Model, None]:
        """An async generator that yields models in topological order."""
        # Iterates over the models in the dataset in topological order

        # Collect the table references of the current models
        model_table_map: dict[str, Model] = {}
        for model in self._models:
            model_table_map[str(model)] = model

        sorter = TopologicalSorter()
        for model in self._models:
            dependencies = await model.dataset_internal_dependencies()
            # Only add dependencies that are in the current set of models
            dependencies_set = set(
                [str(dep) for dep in dependencies if str(dep) in model_table_map]
            )
            sorter.add(str(model), *dependencies_set)

        for table_ref in sorter.static_order():
            yield model_table_map[table_ref]


class UserDefinedModelStateClient(abc.ABC):
    """A client to manage user defined models."""

    @abc.abstractmethod
    async def all_models_missing_runs(self) -> list[Model]:
        raise NotImplementedError(
            "all_models_missing_runs must be implemented by subclasses."
        )


T = t.TypeVar("T", bound=Message)


class StepContext(abc.ABC):
    @property
    @abc.abstractmethod
    def log(self) -> logging.Logger:
        """A logger for the message handler context."""
        raise NotImplementedError("log must be implemented by subclasses.")

    @abc.abstractmethod
    async def create_materialization(
        self, table_id: str, warehouse_fqn: str, schema: list[DataModelColumnInput]
    ) -> CreateMaterialization:
        """A method to add a materialization to the step context."""
        raise NotImplementedError(
            "add_materialization must be implemented by subclasses."
        )

    @property
    @abc.abstractmethod
    def materialization_strategy(self) -> MaterializationStrategy:
        """The materialization strategy for the current step."""
        raise NotImplementedError(
            "materialization_strategy must be implemented by subclasses."
        )

    @property
    @abc.abstractmethod
    def step_id(self) -> str:
        """The ID of the current step."""
        raise NotImplementedError("step_id must be implemented by subclasses.")

    def generate_destination_fqn(self, ref: TableReference) -> str:
        """Generate the destination fully qualified name for a table reference."""
        return self.materialization_strategy.destination_fqn(ref)

    def generate_destination_table_exp(self, ref: TableReference) -> exp.Table:
        """Generate the destination table expression for a table reference."""
        fqn = self.generate_destination_fqn(ref)
        return exp.to_table(fqn)


class RunContext(abc.ABC):
    @abc.abstractmethod
    def step_context(
        self, name: str, display_name: str
    ) -> t.AsyncContextManager[StepContext]:
        """An async context manager for the message handler context."""
        raise NotImplementedError("step_context must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def log(self) -> logging.Logger:
        """A logger for the message handler context."""
        raise NotImplementedError("log must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def materialization_strategy(self) -> MaterializationStrategy:
        """The materialization strategy for the current step."""
        raise NotImplementedError(
            "materialization_strategy must be implemented by subclasses."
        )

    def generate_destination_fqn(self, ref: TableReference) -> str:
        """Generate the destination fully qualified name for a table reference."""
        return self.materialization_strategy.destination_fqn(ref)

    def generate_destination_table_exp(self, ref: TableReference) -> exp.Table:
        """Generate the destination table expression for a table reference."""
        fqn = self.generate_destination_fqn(ref)
        return exp.to_table(fqn)

    def update_metadata(
        self, metadata: dict[str, t.Any], merge: bool
    ) -> t.Awaitable[UpdateRunMetadata]:
        """Updates the run metadata for the current run."""
        raise NotImplementedError("update_metadata must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def run_id(self) -> str:
        """The ID of the current run."""
        raise NotImplementedError("run_id must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def organization(self) -> OrganizationCommon:
        """The organization for the current run."""
        raise NotImplementedError("organization must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def dataset(self) -> DatasetCommon | None:
        """The dataset for the current run."""
        raise NotImplementedError("dataset must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def requested_by(self) -> UserCommon | None:
        """The user who requested the current run."""
        raise NotImplementedError("requested_by must be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def trigger_type(self) -> str:
        """The trigger type for the current run."""
        raise NotImplementedError("trigger_type must be implemented by subclasses.")


class HandlerResponse(BaseModel):
    message: str
    status_code: int = Field(
        description="HTTP-like status code representing the result. 300s are unused."
    )


class AlreadyLockedMessageResponse(HandlerResponse):
    """A response indicating that the message is already being processed by
    another worker. The worker _should_ not update any run status and simply
    nack the message.

    Duplicate messages are expected in google pub/sub as we don't enable exactly-once
    delivery (for now). The assumption is that it's better to be robust to duplicate
    messages than to miss processing a message entirely.
    """

    message: str = Field(
        default="Message is already being processed by another worker."
    )
    status_code: int = Field(default=0)


class SkipResponse(HandlerResponse):
    message: str = Field(
        default="Skipped processing the message. No action is taken on the run by this worker."
    )
    status_code: int = Field(default=204)


class FailedResponse(HandlerResponse):
    message: str = Field(default="Failed to process the message.")
    status_code: int = Field(default=500)
    details: dict[str, t.Any] = Field(default_factory=dict)


class SuccessResponse(HandlerResponse):
    message: str = Field(default="Successfully processed the message.")
    status_code: int = Field(default=200)


class CancelledResponse(HandlerResponse):
    message: str = Field(default="Processing of the message was cancelled.")
    status_code: int = Field(default=499)


class MessageHandler(abc.ABC, t.Generic[T]):
    topic: str
    message_type: t.Type[T]
    schema_file_name: str

    async def handle_message(self, *args, **kwargs) -> HandlerResponse:
        """A method to handle incoming messages"""
        raise NotImplementedError("handle_message must be implemented by subclasses.")

    def new_message(self) -> T:
        """A method to create a new message instance"""
        return self.message_type()

    def parse_binary_message(self, data: bytes) -> T:
        """A method to parse binary encoded messages"""
        destination = self.new_message()
        destination.ParseFromString(data)
        return destination

    def parse_json_message(self, data: bytes | str) -> T:
        """A method to parse JSON encoded messages"""
        destination = self.new_message()
        Parse(data, destination)
        return destination

    def initialize_metrics(self, metrics: MetricsContainer) -> None:
        return None


class MessageHandlerRegistry:
    def __init__(self) -> None:
        self._listeners: dict[str, MessageHandler] = {}

    def register(self, listener: MessageHandler) -> None:
        if listener.topic not in self._listeners:
            self._listeners[listener.topic] = listener
        else:
            raise ValueError(f"Listener for topic {listener.topic} already registered")

    def __iter__(self):
        for topic, listener in self._listeners.items():
            yield (topic, listener)

    def get_handler(self, topic: str) -> MessageHandler | None:
        return self._listeners.get(topic)


class GenericMessageQueueService(abc.ABC):
    def __init__(
        self, resources: ResourcesContext, registry: MessageHandlerRegistry
    ) -> None:
        self.registry = registry
        self.resources = resources

    def get_queue_listener(self, topic: str) -> MessageHandler:
        listener = self.registry.get_handler(topic)
        if not listener:
            raise ValueError(f"No listener registered for topic {topic}")
        metrics = self.resources.resolve("metrics")

        assert isinstance(metrics, MetricsContainer)
        listener.initialize_metrics(metrics)
        return listener

    @abc.abstractmethod
    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue"""
        ...

    @abc.abstractmethod
    async def publish_message(self, queue: str, message: Message) -> None:
        """A method to publish a message to the given queue"""
        ...
