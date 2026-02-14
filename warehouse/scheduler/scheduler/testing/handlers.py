import typing as t

import structlog
from google.protobuf.message import Message
from oso_core.logging.types import BindableLogger
from oso_core.resources import ResourcesRegistry
from scheduler.materialization.duckdb import DuckdbMaterializationStrategy
from scheduler.testing.resources.base import base_testing_resources
from scheduler.types import MessageHandler, RunLoggerContainer, RunLoggerFactory

T = t.TypeVar("T", bound=Message)


class MessageHandlerTestHarness(t.Generic[T]):
    def __init__(self, resources: ResourcesRegistry, handler: MessageHandler[T]):
        self.resources = resources
        self.handler = handler
        self.initialized = False

    def initialize(self):
        if not self.initialized:
            resources_context = self.resources.context()
            resources_context.run(
                self.handler.initialize,
            )
            self.initialized = True

    async def send_message(self, message: T):
        # Simulate sending a message to the handler
        resources_context = self.resources.context()
        self.initialize()

        return await resources_context.run(
            self.handler.handle_message,
            additional_inject={
                "message": message,
                "logger": structlog.get_logger("scheduler.testing"),
                "run_logger_factory": FakeRunLoggerFactory(),
            },
        )


async def async_iter(items: t.List[t.Any]) -> t.AsyncIterator[t.Any]:
    for item in items:
        yield item


class FakeRunLoggerContainer(RunLoggerContainer):
    def __init__(self, run_id: str):
        self._run_id = run_id

    @property
    def logger(self) -> BindableLogger:
        return structlog.get_logger("scheduler.testing").bind(run_id=self._run_id)

    async def destination_uris(self) -> list[str]:
        return []


class FakeRunLoggerFactory(RunLoggerFactory):
    def create_logger_container(self, run_id: str):
        return FakeRunLoggerContainer(run_id)


def default_message_handler_test_harness(
    handler: MessageHandler[T],
    additional_resources: list[tuple[str, t.Any]] | None = None,
) -> MessageHandlerTestHarness[T]:
    resources = base_testing_resources()

    materialization_strategy = DuckdbMaterializationStrategy("test")
    resources.add_singleton(
        "materialization_strategy",
        materialization_strategy,
    )

    if additional_resources:
        for name, resource in additional_resources:
            resources.add_singleton(name, resource)

    return MessageHandlerTestHarness(resources, handler)
