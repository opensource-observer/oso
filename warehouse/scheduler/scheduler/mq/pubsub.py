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
import typing as t
import uuid
from dataclasses import dataclass
from threading import Event, Lock

from google.cloud.pubsub import SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from google.protobuf.message import Message as ProtobufMessage
from janus import AsyncQueue, Queue, SyncQueue
from oso_core.instrumentation import MetricsContainer
from oso_core.instrumentation.timing import async_time
from oso_core.resources import ResourcesContext
from scheduler.types import (
    CancelledResponse,
    FailedResponse,
    GenericMessageQueueService,
    HandlerResponse,
    MessageHandler,
    MessageHandlerRegistry,
    SkipResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)


class _ResponseStorage:
    def __init__(self) -> None:
        self._response: dict[str, HandlerResponse] = {}
        self._lock = Lock()

    def store_response(self, id: str, response: HandlerResponse) -> None:
        with self._lock:
            self._response[id] = response

    def pop_response(self, id: str) -> t.Optional[HandlerResponse]:
        with self._lock:
            return self._response.pop(id, None)


@dataclass
class _QueuedPubSubMessage:
    """An internal structure to represent messages internally queued for
    processing."""

    handle_id: str
    message: Message
    ready: Event


_InternalCallback = t.Callable[
    [SyncQueue[_QueuedPubSubMessage], _ResponseStorage, Message], None
]


class GCPPubSubMessageQueueService(GenericMessageQueueService):
    def __init__(
        self,
        project_id: str,
        resources: ResourcesContext,
        registry: MessageHandlerRegistry,
        metrics: MetricsContainer,
        emulator_enabled: bool = False,
    ) -> None:
        super().__init__(resources, registry)
        self._project_id = project_id
        self._metrics = metrics
        self._emulator_enabled = emulator_enabled

    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue

        Google's implementation of Pub/Sub uses a callback model from threads,
        so our implementation here adapts this by using a queue and events to
        communicate between the callback and the async loop.
        """
        # Implementation for GCP Pub/Sub listening logic goes here

        handler = self.get_queue_listener(queue)

        metrics = self._metrics

        # Initialize metrics for the handler
        handler.initialize_metrics(metrics)

        # We create the queue, event, and response storage here and not as some
        # class state because they exist only in the context of this "run_loop"
        close_event = Event()
        message_queue: Queue[_QueuedPubSubMessage] = Queue()
        response_storage = _ResponseStorage()

        gcp_subscriber_thread = self._start_subscriber_thread(
            message_queue=message_queue,
            response_storage=response_storage,
            queue=queue,
            handler=handler,
            close_event=close_event,
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
                metrics.counter("messages_received_total").inc({})

                asyncio.create_task(
                    self.process_queue_message(
                        metrics,
                        message_count,
                        response_storage,
                        handler,
                        queued_message,
                    )
                )
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info(
                "Shut down signal received. Closing GCP Pub/Sub message listener."
            )
        except Exception as e:
            logger.error(f"Error in GCP Pub/Sub message listener: {e}")
        finally:
            close_event.set()
            await gcp_subscriber_thread
            message_queue.close()

    def _create_message_callback(
        self,
        queue: str,
        handler: MessageHandler[t.Any],
    ) -> _InternalCallback:
        """Creates a message callback function for GCP Pub/Sub messages. That
        has no internal reference to `self` as this will be used in a different
        thread so we want to limit captured state."""

        emulator_enabled = self._emulator_enabled

        def callback(
            message_queue: SyncQueue[_QueuedPubSubMessage],
            response_storage: _ResponseStorage,
            raw_message: Message,
        ) -> None:
            logger.info("Received message: {}".format(raw_message.message_id))

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

            ready_event = Event()

            message_queue.put(
                _QueuedPubSubMessage(
                    handle_id=handle_id, message=message, ready=ready_event
                )
            )

            if not ready_event.wait(timeout=300):
                logger.error(
                    f"Timeout waiting for message processing for message ID: {raw_message.message_id}"
                )
                raw_message.nack()
                return

            response = response_storage.pop_response(handle_id)
            match response:
                case SkipResponse():
                    logger.info("Skipping message processing as per handler response.")
                    raw_message.ack()
                case FailedResponse():
                    raw_message.ack()
                case SuccessResponse():
                    raw_message.ack()
                case _:
                    logger.warning(
                        f"Unhandled response type {type(response)} from message handler."
                    )

        return callback

    def _start_subscriber_thread(
        self,
        *,
        message_queue: Queue[_QueuedPubSubMessage],
        response_storage: _ResponseStorage,
        queue: str,
        handler: MessageHandler[t.Any],
        close_event: Event,
    ) -> asyncio.Task[None]:
        # We declare the function here and avoid capturing `self` in the closure
        def run_subscriber(
            sync_message_queue: SyncQueue[_QueuedPubSubMessage],
            response_storage: _ResponseStorage,
            project_id: str,
            queue: str,
            callback: _InternalCallback,
            close_event: Event,
        ) -> None:
            """Starts the GCP Pub/Sub subscriber to listen for messages."""
            subscriber = SubscriberClient()
            subscription_path = subscriber.subscription_path(project_id, queue)

            partial_callback = functools.partial(
                callback, sync_message_queue, response_storage
            )
            streaming_pull_future = subscriber.subscribe(
                subscription_path, callback=partial_callback
            )
            logger.info(f"Listening for messages on {subscription_path}...")

            with subscriber:
                while True:
                    try:
                        logger.debug("Waiting for messages...")
                        streaming_pull_future.result(timeout=10)
                    except TimeoutError:
                        logger.debug("Timeout reached, checking for close event.")
                        if close_event.is_set():
                            logger.info("GCP Pub/Sub listener is shutting down cleanly")
                            streaming_pull_future.cancel()
                            return
                    except Exception as e:
                        logger.error(
                            f"Listening for messages on {subscription_path} threw an exception: {e}."
                        )
                        streaming_pull_future.cancel()

        callback = self._create_message_callback(queue, handler)

        # Listen for messages on the message queue
        gcp_subscriber_thread = asyncio.create_task(
            asyncio.to_thread(
                run_subscriber,
                message_queue.sync_q,
                response_storage,
                self._project_id,
                queue,
                callback,
                close_event,
            )
        )
        return gcp_subscriber_thread

    async def process_queue_message(
        self,
        metrics: MetricsContainer,
        message_number: int,
        response_storage: _ResponseStorage,
        handler: MessageHandler,
        queued_message: _QueuedPubSubMessage,
    ) -> None:
        metrics.gauge("messages_active").inc({})
        try:
            logger.debug(
                f"Processing queued message #{message_number} {queued_message}",
                extra={"queued_message": queued_message},
            )
            async with async_time(
                metrics.summary("message_handling_duration_ms")
            ) as labeler:
                response = await self.resources.run(
                    handler.handle_message,
                    additional_inject={
                        "message": queued_message.message,
                    },
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

            logger.debug(f"Finished processing queued message #{message_number}")
            await self.record_response(response_storage, queued_message, response)
            response_storage.store_response(queued_message.handle_id, response)
            queued_message.ready.set()
        except Exception as e:
            logger.error(f"Error processing queued message #{message_number}: {e}")
            response_storage.store_response(
                queued_message.handle_id, FailedResponse(message=str(e))
            )
            queued_message.ready.set()
        finally:
            metrics.gauge("messages_active").dec({})

    async def record_response(
        self,
        response_storage: _ResponseStorage,
        queued_message: _QueuedPubSubMessage,
        response: HandlerResponse,
    ) -> None:
        """Records the response for a processed message."""
        response_storage.store_response(queued_message.handle_id, response)
        queued_message.ready.set()

        metrics = self._metrics

        # Record metrics based on response type
        match response:
            case SuccessResponse():
                metrics.counter("messages_processed_total").inc({"status": "success"})
            case FailedResponse():
                metrics.counter("messages_processed_total").inc({"status": "failed"})
            case SkipResponse():
                metrics.counter("messages_processed_total").inc({"status": "skipped"})
            case CancelledResponse():
                metrics.counter("messages_processed_total").inc({"status": "cancelled"})

    async def _get_from_queue_or_timeout(
        self, queue: AsyncQueue[_QueuedPubSubMessage], timeout: float
    ) -> t.Optional[_QueuedPubSubMessage]:
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
        logger.info(f"Published message to {queue} with message ID: {message_id}")
