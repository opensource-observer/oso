"""
Surface level tests for the pubsub mq scheduler component.
"""

import asyncio
import concurrent.futures
import logging
import traceback
import typing as t
from contextlib import asynccontextmanager
from dataclasses import dataclass
from threading import Event
from unittest.mock import Mock

import pytest
from google.cloud.pubsub_v1.subscriber.message import Message as PubSubMessage
from google.protobuf.message import Message
from janus import Queue, SyncQueue, SyncQueueEmpty
from oso_core.instrumentation.container import MetricsContainer
from oso_core.logging.types import BindableLogger
from oso_core.resources import ResourcesRegistry
from osoprotobufs.test_message_pb2 import TestMessageRunRequest
from scheduler.config import CommonSettings
from scheduler.mq.common import RunHandler
from scheduler.mq.pubsub import (
    GCPPubSubMessageQueueService,
    InternalCallback,
    QueuedPubSubMessage,
    ResponseStorage,
    RunSubscriberFn,
)
from scheduler.testing.resources.base import base_testing_resources
from scheduler.testing.resources.logging import FakeRunLoggerFactory
from scheduler.testing.uuids import generate_uuid_as_bytes
from scheduler.types import MessageHandlerRegistry, SuccessResponse
from scheduler.utils import convert_uuid_bytes_to_str

T = t.TypeVar("T", bound=Message)

logger = logging.getLogger(__name__)


class FakePubSubMessage:
    """A fake pub/sub message we can instrospect for testing purposes.

    It was easier to create a fake class than mock the original PubSubMessage class
    """

    def __init__(self, data: bytes, message_id: str = "test_message_id"):
        self._data = data
        self._message_id = message_id
        self.ack_count = 0
        self.nack_count = 0

    @property
    def message_id(self) -> str:
        return self._message_id

    @property
    def attributes(self) -> dict[str, str]:
        return {
            "googclient_schemaencoding": "BINARY",
        }

    @property
    def data(self) -> bytes:
        return self._data

    def ack(self):
        self.ack_count += 1

    def nack(self):
        self.nack_count += 1

    def drop(self, *args, **kwargs):
        pass

    def modify_ack_deadline(self, *args, **kwargs):
        pass


@dataclass
class ControllableSubscriber:
    """A controllable subscriber for testing purposes."""

    test_input_queue: Queue[FakePubSubMessage]
    test_ack_queue: Queue[bool]
    pubsub_mq_service: GCPPubSubMessageQueueService

    @asynccontextmanager
    async def send_message(
        self, queue: str, message: FakePubSubMessage, timeout: float = 60.0
    ):
        """Send a message to the subscriber."""
        loop_task = asyncio.create_task(self.pubsub_mq_service.start(queue))
        logger.info("Waiting for subscriber to start...")
        async with asyncio.timeout(timeout):
            await self.test_input_queue.async_q.put(message)

        try:
            logger.info("Waiting for message to be processed...")
            async with asyncio.timeout(timeout):
                result = await self.test_ack_queue.async_q.get()
                logger.info(f"Message processed with result: {result}")
                yield result
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for message to be processed")
            raise
        finally:
            logger.info("Killing subscriber loop task...")
            loop_task.cancel()
            await loop_task


def pubsub_mq_service_factory(
    resources: ResourcesRegistry,
    run_subscriber_fn: RunSubscriberFn,
    message_handler_registry: MessageHandlerRegistry,
):
    metrics = resources.context().resolve_with_type("metrics", MetricsContainer)

    resources_context = resources.context()

    return GCPPubSubMessageQueueService(
        resources=resources_context,
        registry=message_handler_registry,
        metrics=metrics,
        project_id="test-project",
        run_subscriber_fn=run_subscriber_fn,
    )


def run_subscriber_factory(
    input_queue: SyncQueue[FakePubSubMessage],
    test_ack_queue: SyncQueue[bool],
) -> RunSubscriberFn:
    """Simulates a subscriber thread that receives messages by reading from
    the input queue"""

    def _inner_run_subscriber(
        message_queue: SyncQueue[QueuedPubSubMessage],
        response_storage: ResponseStorage,
        _project_id: str,
        _queue: str,
        ack_deadline_seconds: int,
        logger: BindableLogger,
        callback: InternalCallback,
        close_event: Event,
    ):
        logger.debug("Fake subscriber started")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            while True:
                try:
                    item = input_queue.get(timeout=0.5)
                    logger.info(f"Fake subscriber received item: {item}")
                except SyncQueueEmpty:
                    logger.info("Fake subscriber queue empty")
                    item = None
                except Exception as e:
                    logger.error(
                        f"Fake subscriber encountered error: {type(e)}: {str(e)}"
                    )
                    print(traceback.format_exc())
                    break
                if item is None:
                    if close_event.is_set():
                        logger.info("Fake subscriber closing")
                        break
                    continue

                # execute callback in a thread similar to how the real subscriber would
                future = executor.submit(
                    callback,
                    message_queue,
                    response_storage,
                    60,  # ack deadline seconds
                    logger,
                    t.cast(PubSubMessage, item),
                )

                try:
                    future.result(timeout=100)
                    if item.ack_count > 0:
                        test_ack_queue.put(True)
                    elif item.nack_count > 0:
                        test_ack_queue.put(False)
                    else:
                        raise RuntimeError("Message was neither acked nor nacked")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    raise

    return _inner_run_subscriber


@pytest.fixture
def controllable_subscriber(
    base_resources: ResourcesRegistry, message_handler_registry: MessageHandlerRegistry
) -> ControllableSubscriber:
    test_input_queue: Queue[FakePubSubMessage] = Queue()
    test_ack_queue: Queue[bool] = Queue()

    run_subscriber = run_subscriber_factory(
        test_input_queue.sync_q, test_ack_queue.sync_q
    )

    # Add some additional dummy resources
    materialization_strategy = Mock()
    base_resources.add_singleton(
        "materialization_strategy",
        materialization_strategy,
    )
    base_resources.add_singleton(
        "run_logger_factory",
        FakeRunLoggerFactory(),
    )

    return ControllableSubscriber(
        test_input_queue=test_input_queue,
        test_ack_queue=test_ack_queue,
        pubsub_mq_service=pubsub_mq_service_factory(
            resources=base_resources,
            run_subscriber_fn=run_subscriber,
            message_handler_registry=message_handler_registry,
        ),
    )


class FakeRunHandler(RunHandler[TestMessageRunRequest]):
    topic = "test_topic"
    message_type = TestMessageRunRequest 
    schema_file_name = "test-message.proto"

    async def handle_run_message(
        self,
        message: TestMessageRunRequest,
        **kwargs,
    ):
        logger.info(f"Sleeping for {message.sleep_seconds} seconds to simulate work...")
        logger.info(f"Message __dict__ : {message.run_id}")
        await asyncio.sleep(message.sleep_seconds)

        run_id = convert_uuid_bytes_to_str(message.run_id)

        return SuccessResponse(
            message=f"Handled message with run_id: {run_id}",
        )


@pytest.fixture
def message_handler_registry():
    registry = MessageHandlerRegistry()
    registry.register(FakeRunHandler())
    return registry


@pytest.fixture
def base_resources():
    return base_testing_resources()


@pytest.mark.asyncio
async def test_gcp_pubsub_scheduler_receives_message(
    controllable_subscriber: ControllableSubscriber,
):
    """Test that a message published to a GCP Pub/Sub topic is received by the scheduler."""

    test_message_run_request = TestMessageRunRequest(
        run_id=generate_uuid_as_bytes(),
        sleep_seconds=0,
    )

    fake_message = FakePubSubMessage(data=test_message_run_request.SerializeToString())

    async with controllable_subscriber.send_message(
        queue="test_topic",
        message=fake_message,
        timeout=3,
    ) as acked:
        assert acked is True

@pytest.mark.asyncio
async def test_gcp_pubsub_scheduler_times_out_processing(
    controllable_subscriber: ControllableSubscriber, base_resources: ResourcesRegistry
):
    """Test that a message published to a GCP Pub/Sub topic is received by the scheduler."""

    common_settings = base_resources.context().resolve_with_type(
        "common_settings", CommonSettings
    )
    common_settings.message_handling_timeout_seconds = 1


    test_message_run_request = TestMessageRunRequest(
        run_id=generate_uuid_as_bytes(),
        sleep_seconds=60,
    )

    fake_message = FakePubSubMessage(data=test_message_run_request.SerializeToString())

    async with controllable_subscriber.send_message(
        queue="test_topic",
        message=fake_message,
        timeout=1000,
    ) as acked:
        assert acked is False
