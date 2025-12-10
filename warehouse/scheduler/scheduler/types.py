import abc
import typing as t

from google.protobuf.json_format import Parse
from google.protobuf.message import Message
from oso_core.resources import ResourcesContext
from pydantic import BaseModel
from sqlglot import exp, parse_one
from sqlglot.optimizer.qualify_columns import qualify_columns
from sqlglot.optimizer.scope import build_scope
from sqlmesh.core import dialect as sqlmesh_dialect


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

    def __init__(self, *args: t.Any, **data: t.Any):
        super().__init__(*args, **data)
        self._parsed_query = None

    @property
    def query(self):
        if self._parsed_query is None:
            parsed = parse_one(self.code)
            assert isinstance(parsed, exp.Query)
            self._parsed_query = t.cast(exp.Query, parsed)
        return self._parsed_query

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


class UserDefinedModelStateClient(abc.ABC):
    """A client to manage user defined models."""

    @abc.abstractmethod
    async def all_models_missing_runs(self) -> list[Model]:
        raise NotImplementedError(
            "all_models_missing_runs must be implemented by subclasses."
        )


T = t.TypeVar("T", bound=Message)


class AsyncMessageQueueHandler(abc.ABC, t.Generic[T]):
    topic: str
    message_type: t.Type[T]

    @abc.abstractmethod
    async def handle_message(self, *, message: T, **kwargs) -> None: ...

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


class MessageQueueHandlerRegistry:
    def __init__(self) -> None:
        self._listeners: dict[str, AsyncMessageQueueHandler] = {}

    def register(self, listener: AsyncMessageQueueHandler) -> None:
        if listener.topic not in self._listeners:
            self._listeners[listener.topic] = listener
        else:
            raise ValueError(f"Listener for topic {listener.topic} already registered")

    def get_handler(self, topic: str) -> AsyncMessageQueueHandler | None:
        return self._listeners.get(topic)


class GenericMessageQueueService(abc.ABC):
    def __init__(
        self, resources: ResourcesContext, registry: MessageQueueHandlerRegistry
    ) -> None:
        self.registry = registry
        self.resources = resources

    def get_queue_listener(self, topic: str) -> AsyncMessageQueueHandler:
        listener = self.registry.get_handler(topic)
        if not listener:
            raise ValueError(f"No listener registered for topic {topic}")
        return listener

    @abc.abstractmethod
    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue"""
        ...

    @abc.abstractmethod
    async def publish_message(self, queue: str, message: Message) -> None:
        """A method to publish a message to the given queue"""
        ...
