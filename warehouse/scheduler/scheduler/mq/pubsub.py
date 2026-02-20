"""
A message queue service implementation using Google Cloud Pub/Sub.

Due to the way the Google Cloud Pub/Sub client library is designed, this
implementation has to use a complex set of techniques to attempt to maintain the
async interface that we expect from our `GenericMessageQueueService` derived
classes. The main problems at the time of writing are:

* The Pub/Sub client library uses a callback model for message handling,
    where it submits the callback to a thread pool
* We use the `ResourcesContext` which isn't inherently thread-safe, but can
    be made thread aware. However, if we just use the thread pool we don't have
    a way to easily take over the thread pool invocation and ensure that you're
    only interacting with the correct `ResourcesContext` in the correct event
    loop.

To work around these issues, this implementation uses a `janus.Queue` to
communicate between the Pub/Sub callback threads and an async loop that we run
in the main event loop. The callback puts messages onto the `SyncQueue` which is
a synchronous projection of the `janus.Queue`, and the async loop reads from the
`AsyncQueue` which is the asynchronous projection. Using this queuing internally
we can still process _many_ messages concurrently. Start times will be
serialized by the queue, but once a message has kicked off processing, any
blocking io will allow for the python async coroutines to switch contexts as
needed.
"""

import asyncio
import functools
import logging
import time
import typing as t
import uuid
from dataclasses import dataclass
from queue import Empty as PythonQueueEmpty
from queue import Queue as PythonQueue
from threading import Event, Lock

import structlog
from aioprometheus.collectors import Counter, Gauge, Histogram
from google.cloud.pubsub import SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from google.protobuf.message import Message as ProtobufMessage
from janus import AsyncQueue, Queue, SyncQueue
from oso_core.instrumentation import MetricsContainer
from oso_core.instrumentation.timing import async_time
from oso_core.logging.types import BindableLogger
from oso_core.resources import ResourcesContext
from scheduler.config import CommonSettings
from scheduler.types import (
    AlreadyLockedMessageResponse,
    CancelledResponse,
    FailedResponse,
    GenericMessageQueueService,
    HandlerResponse,
    MessageHandler,
    MessageHandlerRegistry,
    SkipResponse,
    SuccessResponse,
    TimeoutCancellation,
)

module_logger = logging.getLogger(__name__)


class ResponseStorage:
    def __init__(self) -> None:
        self._response: dict[str, HandlerResponse] = {}
        self._lock = Lock()

    def store_response(self, id: str, response: HandlerResponse) -> None:
        with self._lock:
            self._response[id] = response

    def pop_response(self, id: str) -> t.Optional[HandlerResponse]:
        with self._lock:
            return self._response.pop(id, None)


type QueuedMessageEvent = t.Literal["heartbeat", "completed", "cancelled"]


@dataclass
class QueuedPubSubMessage:
    """An internal structure to represent messages internally queued for
    processing."""

    handle_id: str
    message_id: str
    message: Message
    event_queue: PythonQueue[QueuedMessageEvent]


InternalCallback = t.Callable[
    [SyncQueue[QueuedPubSubMessage], ResponseStorage, int, BindableLogger, Message],
    None,
]


def run_subscriber(
    sync_message_queue: SyncQueue[QueuedPubSubMessage],
    response_storage: ResponseStorage,
    project_id: str,
    queue: str,
    ack_deadline_seconds: int,
    logger: BindableLogger,
    callback: InternalCallback,
    close_event: Event,
) -> None:
    """Starts the GCP Pub/Sub subscriber to listen for messages.

    This is designed to run in a separate thread, as the Pub/Sub client library
    uses a callback model that is not inherently async.

    Args:
        sync_message_queue: The synchronous queue to put received messages onto.
        response_storage: The storage to keep track of message processing responses.
        project_id: The GCP project ID.
        queue: The Pub/Sub subscription name.
        callback: The callback function to handle received messages.
        close_event: An event to signal when to stop listening for messages.

    Returns:
        None

    This is declared to enable replacement of this subscriber function in tests.
    """
    subscriber = SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, queue)

    partial_callback = functools.partial(
        callback,
        sync_message_queue,
        response_storage,
        ack_deadline_seconds,
        logger.bind(thread="_gcp_callback"),
    )
    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=partial_callback
    )
    module_logger.info(f"Listening for messages on {subscription_path}...")

    with subscriber:
        while True:
            try:
                module_logger.debug("Waiting for messages...")
                streaming_pull_future.result(timeout=10)
            except TimeoutError:
                module_logger.debug("Timeout reached, checking for close event.")
                if close_event.is_set():
                    module_logger.info("GCP Pub/Sub listener is shutting down cleanly")
                    streaming_pull_future.cancel()
                    return
            except Exception as e:
                module_logger.error(
                    f"Listening for messages on {subscription_path} threw an exception: {e}."
                )
                streaming_pull_future.cancel()


RunSubscriberFn = t.Callable[
    [
        SyncQueue[QueuedPubSubMessage],
        ResponseStorage,
        str,
        str,
        int,
        BindableLogger,
        InternalCallback,
        Event,
    ],
    None,
]


class GCPPubSubMessageQueueService(GenericMessageQueueService):
    def __init__(
        self,
        project_id: str,
        resources: ResourcesContext,
        registry: MessageHandlerRegistry,
        metrics: MetricsContainer,
        emulator_enabled: bool = False,
        run_subscriber_fn: RunSubscriberFn = run_subscriber,
    ) -> None:
        super().__init__(resources, registry)
        self._project_id = project_id
        self._metrics = metrics
        self._emulator_enabled = emulator_enabled
        self._run_subscriber_fn = run_subscriber_fn

    def initialize(self, metrics: MetricsContainer):
        metrics.initialize_counter(
            Counter(
                "pubsub_messages_received_total",
                "Total number of Pub/Sub messages received",
            )
        )
        metrics.initialize_counter(
            Counter(
                "pubsub_messages_processed_total",
                "Total number of Pub/Sub messages processed",
            )
        )
        metrics.initialize_gauge(
            Gauge(
                "pubsub_messages_active",
                "Number of Pub/Sub messages currently being processed",
            )
        )
        metrics.initialize_histogram(
            Histogram(
                "pubsub_message_handling_duration_ms",
                "Duration of Pub/Sub message handling in milliseconds",
            )
        )

    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue

        Google's implementation of Pub/Sub uses a callback model from threads,
        so our implementation here adapts this by using a queue and events to
        communicate between the callback and the async loop.
        """
        # Implementation for GCP Pub/Sub listening logic goes here

        handler = self.initialize_queue_handler(self.resources, queue)

        common_settings = t.cast(
            CommonSettings, self.resources.resolve("common_settings")
        )

        metrics = self._metrics
        logger: BindableLogger = structlog.get_logger(
            f"scheduler.{handler.topic}"
        ).bind(thread="main")

        # We create the queue, event, and response storage here and not as some
        # class state because they exist only in the context of this "run_loop"
        close_event = Event()
        message_queue: Queue[QueuedPubSubMessage] = Queue()
        response_storage = ResponseStorage()

        gcp_subscriber_thread = self._start_subscriber_thread(
            message_queue=message_queue,
            response_storage=response_storage,
            queue=queue,
            handler=handler,
            close_event=close_event,
            common_settings=common_settings,
            # Not sure if this actually creates a different instance for the
            # thread but we want to know if the logger is in the subscriber
            # thread or not for debugging purposes
            logger=structlog.get_logger(f"scheduler.{handler.topic}").bind(
                thread="_gcp_subscriber"
            ),
        )

        # Just a counter for logging purposes
        message_count = 0

        try:
            # Start the loop to process messages from the janus.Queue
            while True:
                queued_message = await self._get_from_queue_or_timeout(
                    message_queue.async_q, timeout=10
                )
                if not queued_message:
                    # Check if the subscriber thread is still running
                    if gcp_subscriber_thread.done():
                        logger.info(
                            "GCP Pub/Sub subscriber thread has terminated unexpectedly. Exiting message loop."
                        )
                        break
                    continue

                message_count += 1
                metrics.counter("pubsub_messages_received_total").inc({})

                asyncio.create_task(
                    self.process_queue_message(
                        common_settings,
                        metrics,
                        message_count,
                        response_storage,
                        handler,
                        queued_message,
                        logger.bind(gcp_message_id=queued_message.message_id),
                    )
                )
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info(
                "Shut down signal received. Closing GCP Pub/Sub message listener."
            )
        except Exception as e:
            logger.error(f"Error in GCP Pub/Sub message listener: {e}")
            raise
        finally:
            close_event.set()
            await gcp_subscriber_thread
            message_queue.close()

    def _create_message_callback(
        self, queue: str, handler: MessageHandler[t.Any]
    ) -> InternalCallback:
        """Creates a message callback function for GCP Pub/Sub messages. That
        has no internal reference to `self` as this will be used in a different
        thread so we want to limit captured state."""

        emulator_enabled = self._emulator_enabled

        def callback(
            message_queue: SyncQueue[QueuedPubSubMessage],
            response_storage: ResponseStorage,
            ack_deadline_seconds: int,
            logger: BindableLogger,
            raw_message: Message,
        ) -> None:
            logger.info("Received message: {}".format(raw_message.message_id))

            logger = logger.bind(gcp_message_id=str(raw_message.message_id))

            # Get the message serialization type.
            encoding = raw_message.attributes.get("googclient_schemaencoding")
            # Deserialize the message data accordingly.
            if encoding == "BINARY" or emulator_enabled:
                message = handler.parse_binary_message(raw_message.data)
                logger.debug(f"Received binary message on {queue}: {message}")
            elif encoding == "JSON":
                message = handler.parse_json_message(raw_message.data)
                logger.debug(f"Received JSON message on {queue}: {message}")
            else:
                raw_message.ack()
                return

            # Generate a unique handle ID for this message processing
            handle_id = uuid.uuid4().hex

            event_queue: PythonQueue[QueuedMessageEvent] = PythonQueue()

            message_queue.put(
                QueuedPubSubMessage(
                    handle_id=handle_id,
                    message_id=str(raw_message.message_id),
                    message=message,
                    event_queue=event_queue,
                )
            )

            # We force the pubsub library to stop using lease management and
            # we will handle it ourselves (for some reason google's lib can't be
            # trusted to do it well enough). This method doesn't drop the
            # message just the lease management, so we can manage the lease
            # manually without interference from the library.
            raw_message.drop()

            # We set an initial ack deadline to give us some time to process the message
            raw_message.modify_ack_deadline(ack_deadline_seconds)

            while True:
                try:
                    event = event_queue.get(timeout=ack_deadline_seconds)
                except PythonQueueEmpty:
                    # This means the process has taken too long and we should
                    # consider this message processing dead
                    raise TimeoutError(
                        f"Timeout waiting for message processing heartbeat or completion for message ID: {raw_message.message_id}"
                    )
                if event == "cancelled":
                    logger.info(
                        f"Message processing cancelled intentionally for message ID: {raw_message.message_id}. Acknowledging message and stopping processing."
                    )
                    raw_message.ack()
                    return
                elif event == "completed":
                    logger.info(
                        f"Message processing complete and ready for further processing for message ID: {raw_message.message_id}."
                    )
                    break
                raw_message.modify_ack_deadline(ack_deadline_seconds)

            response = response_storage.pop_response(handle_id)
            match response:
                case AlreadyLockedMessageResponse():
                    logger.info(
                        "Message processing skipped due to existing lock. Skipping without acknowledgment."
                    )
                    # Send no nack to prevent immediate redelivery since we
                    # are already processing this message with a different handler.
                case SkipResponse():
                    logger.info("Skipping message processing as per handler response.")
                    raw_message.ack()
                case FailedResponse():
                    logger.error("Error processing message. Acking failure")
                    raw_message.ack()
                case SuccessResponse():
                    logger.debug("Successful response. Sending Ack to pubsub")
                    raw_message.ack()
                case _:
                    logger.warning(
                        f"Unhandled response type {type(response)} from message handler."
                    )

        return callback

    def _start_subscriber_thread(
        self,
        *,
        common_settings: CommonSettings,
        message_queue: Queue[QueuedPubSubMessage],
        response_storage: ResponseStorage,
        queue: str,
        handler: MessageHandler[t.Any],
        logger: BindableLogger,
        close_event: Event,
    ) -> asyncio.Task[None]:
        # We declare the function here and avoid capturing `self` in the closure

        callback = self._create_message_callback(
            queue,
            handler,
        )

        ack_deadline_seconds = int(
            common_settings.message_handling_heartbeat_interval_seconds
            * common_settings.message_handling_heartbeat_buffer_factor
        )

        # Listen for messages on the message queue
        gcp_subscriber_thread = asyncio.create_task(
            asyncio.to_thread(
                self._run_subscriber_fn,
                message_queue.sync_q,
                response_storage,
                self._project_id,
                queue,
                ack_deadline_seconds,
                logger,
                callback,
                close_event,
            )
        )
        return gcp_subscriber_thread

    async def process_queue_message(
        self,
        common_settings: CommonSettings,
        metrics: MetricsContainer,
        message_number: int,
        response_storage: ResponseStorage,
        handler: MessageHandler,
        queued_message: QueuedPubSubMessage,
        logger: BindableLogger,
    ) -> None:
        metrics.gauge("pubsub_messages_active").inc({})

        response = None
        try:
            logger.debug(
                f"Processing queued message #{message_number} {queued_message}",
                extra={"queued_message": queued_message},
            )
            async with async_time(
                metrics.histogram("pubsub_message_handling_duration_ms")
            ) as labeler:
                response = await self._handle_message_with_heartbeat(
                    common_settings,
                    logger,
                    handler,
                    queued_message,
                )
                match response:
                    case SuccessResponse():
                        labeler.add_labels({"status": "success"})
                    case FailedResponse():
                        labeler.add_labels({"status": "failed"})
                    case SkipResponse():
                        labeler.add_labels({"status": "skipped"})
                    case CancelledResponse():
                        labeler.add_labels({"status": "cancelled"})
                    case AlreadyLockedMessageResponse():
                        labeler.add_labels({"status": "locked"})

            logger.debug(f"Finished processing queued message #{message_number}")

        except Exception as e:
            logger.error(f"Error processing queued message #{message_number}: {e}")
            response = FailedResponse(exception=e, message=str(e))
        finally:
            if not response:
                response = FailedResponse(
                    message="Fatal: message processing failed without exception"
                )
            await self.record_response(response_storage, queued_message, response)
            metrics.gauge("pubsub_messages_active").dec({})

    async def _handle_message_with_heartbeat(
        self,
        common_settings: CommonSettings,
        logger: BindableLogger,
        handler: MessageHandler,
        queued_message: QueuedPubSubMessage,
    ) -> HandlerResponse:
        handle_message_task = asyncio.create_task(
            self.resources.run(
                handler.handle_message,
                additional_inject={
                    "message": queued_message.message,
                    "logger": logger,
                },
            )
        )

        message_handling_deadline_time = (
            time.time() + common_settings.message_handling_timeout_seconds
        )
        # Send heartbeats to the callback to keep the Pub/Sub message lease
        # alive while processing
        done, pending = await asyncio.wait(
            [handle_message_task],
            timeout=common_settings.message_handling_heartbeat_interval_seconds,
        )
        while len(pending) > 0 and time.time() < message_handling_deadline_time:
            logger.debug("Sending heartbeat to keep Pub/Sub message lease alive")
            queued_message.event_queue.put("heartbeat")
            done, pending = await asyncio.wait(
                [handle_message_task],
                timeout=common_settings.message_handling_heartbeat_interval_seconds,
            )
        if handle_message_task not in done:
            logger.error(
                f"Message processing task did not complete within the timeout of {common_settings.message_handling_timeout_seconds} seconds."
            )
            handle_message_task.cancel(TimeoutCancellation())

        try:
            async with asyncio.timeout(
                common_settings.message_cancellation_timeout_seconds
            ):
                return await handle_message_task
        except asyncio.TimeoutError:
            logger.error(
                "Fatal: message processing task was likely cancelled but did not finish within the cancellation timeout. Returning FailedResponse."
            )
            return FailedResponse(
                message="Message processing timed out, was cancelled, but failed to response. Forcibly exiting."
            )

    async def record_response(
        self,
        response_storage: ResponseStorage,
        queued_message: QueuedPubSubMessage,
        response: HandlerResponse,
    ) -> None:
        """Records the response for a processed message."""
        response_storage.store_response(queued_message.handle_id, response)
        queued_message.event_queue.put("completed")

        metrics = self._metrics

        # Record metrics based on response type
        match response:
            case SuccessResponse():
                metrics.counter("pubsub_messages_processed_total").inc(
                    {"status": "success"}
                )
            case FailedResponse():
                metrics.counter("pubsub_messages_processed_total").inc(
                    {"status": "failed"}
                )
            case SkipResponse():
                metrics.counter("pubsub_messages_processed_total").inc(
                    {"status": "skipped"}
                )
            case CancelledResponse():
                metrics.counter("pubsub_messages_processed_total").inc(
                    {"status": "cancelled"}
                )
            case AlreadyLockedMessageResponse():
                metrics.counter("pubsub_messages_processed_total").inc(
                    {"status": "locked"}
                )

    async def _get_from_queue_or_timeout(
        self, queue: AsyncQueue[QueuedPubSubMessage], timeout: float
    ) -> t.Optional[QueuedPubSubMessage]:
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def publish_message(self, queue: str, message: ProtobufMessage) -> None:
        """Publishes a message to the given queue."""
        # Implementation for GCP Pub/Sub publishing logic goes here
        from google.cloud import pubsub_v1

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self._project_id, queue)

        # Serialize the message to binary
        message_data = message.SerializeToString()

        # Publish the message
        future = publisher.publish(topic_path, message_data)
        message_id = future.result()
        module_logger.info(
            f"Published message to {queue} with message ID: {message_id}"
        )
