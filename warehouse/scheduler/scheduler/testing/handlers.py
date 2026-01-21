import logging
import typing as t
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import create_autospec

from aiotrino.dbapi import Connection as AsyncConnection
from google.protobuf.message import Message
from oso_core.instrumentation.container import MetricsContainer
from oso_core.resources import ResourcesRegistry
from oso_dagster.resources.trino import TrinoResource
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

        await resources_context.run(
            self.handler.handle_message,
            additional_inject={"message": message},
        )

        await self.handler.handle_message(message=message)


class FakeTrinoResource(TrinoResource):
    @classmethod
    def create(cls) -> "FakeTrinoResource":
        async_connection_mock = create_autospec(AsyncConnection, instance=True)
        sync_connection_mock = create_autospec(Connection, instance=True)
        return cls(
            async_connection_mock=async_connection_mock,
            sync_connection_mock=sync_connection_mock,
        )

    def __init__(
        self,
        async_connection_mock: t.Any,
        sync_connection_mock: t.Any,
    ):
        self.async_connection_mock = async_connection_mock
        self.sync_connection_mock = sync_connection_mock

    @contextmanager
    def get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.Iterator[Connection]:
        yield self.sync_connection_mock

    @asynccontextmanager
    async def get_async_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.AsyncIterator[AsyncConnection]:
        yield self.async_connection_mock


def message_handler_test_harness(
    handler: MessageHandler[T],
    additional_resources: list[tuple[str, t.Any]] | None = None,
) -> MessageHandlerTestHarness[T]:
    metrics = MetricsContainer()
    resources = ResourcesRegistry()
    resources.add_singleton("metrics", metrics)

    oso_client = FakeClientProtocol()
    resources.add_singleton("oso_client", oso_client)

    if additional_resources:
        for name, resource in additional_resources:
            resources.add_singleton(name, resource)

    return MessageHandlerTestHarness(resources, handler)
