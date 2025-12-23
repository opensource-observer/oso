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
from oso_core.resources import ResourcesContext
from scheduler.types import (
    FailedResponse,
    GenericMessageQueueService,
    HandlerResponse,
    MessageHandler,
    MessageHandlerRegistry,
    SkipResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)


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


@dataclass
class QueuedMessage:
    handle_id: str
    message: Message
    ready: Event


def run_subscriber(
    message_queue: SyncQueue[QueuedMessage],
    response_storage: ResponseStorage,
    project_id: str,
    queue: str,
    callback: t.Callable[[SyncQueue[QueuedMessage], ResponseStorage, Message], None],
    close_event: Event,
) -> None:
    subscriber = SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, queue)

    partial_callback = functools.partial(callback, message_queue, response_storage)
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


class GCPPubSubMessageQueueService(GenericMessageQueueService):
    def __init__(
        self,
        project_id: str,
        resources: ResourcesContext,
        registry: MessageHandlerRegistry,
        emulator_enabled: bool = False,
    ) -> None:
        super().__init__(resources, registry)
        self.project_id = project_id
        self.emulator_enabled = emulator_enabled
        self._response_storage = ResponseStorage()
        self._message_queue: Queue[QueuedMessage] = Queue()

    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue

        Google's implementation of Pub/Sub uses a callback model from threads,
        so our implementation here adapts this by using a queue and events to
        communicate between the callback and the async loop.
        """
        # Implementation for GCP Pub/Sub listening logic goes here

        handler = self.get_queue_listener(queue)
        close_event = Event()

        def callback(
            message_queue: SyncQueue[QueuedMessage],
            response_storage: ResponseStorage,
            raw_message: Message,
        ) -> None:
            logger.info("Received message: {}".format(raw_message.message_id))

            # Get the message serialization type.
            encoding = raw_message.attributes.get("googclient_schemaencoding")
            # Deserialize the message data accordingly.
            if encoding == "BINARY" or self.emulator_enabled:
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
                QueuedMessage(handle_id=handle_id, message=message, ready=ready_event)
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

        # Listen for messages on the message queue
        gcp_subscriber_thread = asyncio.create_task(
            asyncio.to_thread(
                run_subscriber,
                self._message_queue.sync_q,
                self._response_storage,
                self.project_id,
                queue,
                callback,
                close_event,
            )
        )

        try:
            while True:
                queued_message = await self._get_from_queue_or_timeout(
                    self._message_queue.async_q, timeout=10
                )
                if not queued_message:
                    # Check if the subscriber thread is still running
                    if gcp_subscriber_thread.done():
                        logger.info(
                            "GCP Pub/Sub subscriber thread has terminated unexpectedly. Exiting message loop."
                        )
                        break
                    continue
                asyncio.create_task(self.process_queue_message(handler, queued_message))
        except KeyboardInterrupt:
            logger.info(
                "Shut down signal received. Closing GCP Pub/Sub message listener."
            )
        except asyncio.CancelledError:
            logger.info(
                "Shut down signal received. Closing GCP Pub/Sub message listener."
            )
        except Exception as e:
            logger.error(f"Error in GCP Pub/Sub message listener: {e}")
        finally:
            close_event.set()
            await gcp_subscriber_thread
            self._message_queue.close()

    async def process_queue_message(
        self, handler: MessageHandler, queued_message: QueuedMessage
    ) -> None:
        try:
            logger.debug(
                f"Processing queued message {queued_message}",
                extra={"queued_message": queued_message},
            )
            response = await self.resources.run(
                handler.handle_message,
                additional_inject={
                    "message": queued_message.message,
                },
            )

            self._response_storage.store_response(queued_message.handle_id, response)
            queued_message.ready.set()
        except Exception as e:
            logger.error(f"Error processing queued message: {e}")
            self._response_storage.store_response(
                queued_message.handle_id, FailedResponse(message=str(e))
            )
            queued_message.ready.set()

    async def _get_from_queue_or_timeout(
        self, queue: AsyncQueue[QueuedMessage], timeout: float
    ) -> t.Optional[QueuedMessage]:
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def publish_message(self, queue: str, message: ProtobufMessage) -> None:
        """Publishes a message to the given queue."""
        # Implementation for GCP Pub/Sub publishing logic goes here
        from google.cloud import pubsub_v1

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self.project_id, queue)

        # Serialize the message to binary
        message_data = message.SerializeToString()

        # Publish the message
        future = publisher.publish(topic_path, message_data)
        message_id = future.result()
        logger.info(f"Published message to {queue} with message ID: {message_id}")
