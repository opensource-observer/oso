import logging
import typing as t
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import AsyncMock, Mock, create_autospec

from aiotrino.dbapi import ColumnDescription
from aiotrino.dbapi import Connection as AsyncConnection
from google.protobuf.message import Message
from oso_core.instrumentation.container import MetricsContainer
from oso_core.resources import ResourcesRegistry
from scheduler.config import CommonSettings
from scheduler.graphql_client.base_model import UnsetType
from scheduler.graphql_client.resolve_tables import ResolveTables
from scheduler.materialization.duckdb import DuckdbMaterializationStrategy
from scheduler.testing.oso_client import FakeClientProtocol
from scheduler.types import MessageHandler
from trino.dbapi import Connection

T = t.TypeVar("T", bound=Message)


class MessageHandlerTestHarness(t.Generic[T]):
    def __init__(self, resources: ResourcesRegistry, handler: MessageHandler[T]):
        self.resources = resources
        self.handler = handler

    async def send_message(self, message: T):
        # Simulate sending a message to the handler
        resources_context = self.resources.context()

        metrics = resources_context.resolve_with_type("metrics", MetricsContainer)

        self.handler.initialize_metrics(metrics)

        return await resources_context.run(
            self.handler.handle_message,
            additional_inject={"message": message},
        )


async def async_iter(items: t.List[t.Any]) -> t.AsyncIterator[t.Any]:
    for item in items:
        yield item


class FakeTrinoResource:
    @classmethod
    def create(cls) -> "FakeTrinoResource":
        async_connection_mock = create_autospec(AsyncConnection, instance=True)
        sync_connection_mock = create_autospec(Connection, instance=True)
        async_cursor_mock = AsyncMock()
        sync_cursor_mock = Mock()
        async_cursor_mock.fetchone.side_effect = [[1], None]
        async_cursor_mock.get_description.return_value = [
            ColumnDescription(
                name="col1",
                type_code=1,
                display_size=2,
                internal_size=2,
                precision=0,
                scale=1,
                null_ok=False,
            ),
        ]
        async_cursor_mock.execute.return_value = async_cursor_mock

        async_connection_mock.cursor.return_value = async_cursor_mock
        sync_connection_mock.cursor.return_value = sync_cursor_mock

        return cls(
            async_connection_mock=async_connection_mock,
            sync_connection_mock=sync_connection_mock,
            async_cursor_mock=async_cursor_mock,
            sync_cursor_mock=sync_cursor_mock,
        )

    def __init__(
        self,
        async_connection_mock: t.Any,
        sync_connection_mock: t.Any,
        async_cursor_mock: t.Any,
        sync_cursor_mock: t.Any,
    ):
        self.async_connection_mock = async_connection_mock
        self.sync_connection_mock = sync_connection_mock
        self.async_cursor_mock = async_cursor_mock
        self.sync_cursor_mock = sync_cursor_mock

    @contextmanager
    def get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.Iterator[Connection]:
        yield self.sync_connection_mock

    @asynccontextmanager
    async def async_get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
        user: t.Optional[str] = None,
    ) -> t.AsyncIterator[AsyncConnection]:
        yield self.async_connection_mock


class FakeOSOClient(FakeClientProtocol):
    async def resolve_tables(
        self,
        references: list[str],
        metadata: t.Union[t.Optional[t.Any], UnsetType] = None,
        **kwargs,
    ) -> ResolveTables:
        from scheduler.graphql_client import (
            ResolveTablesSystem,
            ResolveTablesSystemResolveTables,
        )

        return ResolveTables(
            system=ResolveTablesSystem(
                resolveTables=[
                    ResolveTablesSystemResolveTables(
                        reference=table_name,
                        fqn=table_name,
                    )
                    for table_name in references
                ]
            )
        )


def message_handler_test_harness(
    handler: MessageHandler[T],
    additional_resources: list[tuple[str, t.Any]] | None = None,
) -> MessageHandlerTestHarness[T]:
    metrics = MetricsContainer()
    resources = ResourcesRegistry()

    common_settings = CommonSettings(
        oso_api_url="",
        gcp_project_id="",
    )

    resources.add_singleton("common_settings", common_settings)

    resources.add_singleton("metrics", metrics)

    oso_client = FakeOSOClient()
    resources.add_singleton("oso_client", oso_client)

    materialization_strategy = DuckdbMaterializationStrategy("test")
    resources.add_singleton(
        "materialization_strategy",
        materialization_strategy,
    )

    if additional_resources:
        for name, resource in additional_resources:
            resources.add_singleton(name, resource)

    return MessageHandlerTestHarness(resources, handler)
