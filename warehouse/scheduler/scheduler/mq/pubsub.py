import logging

from google.cloud.pubsub import SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from google.protobuf.message import Message as ProtobufMessage
from oso_core.asynctools import safe_run_until_complete
from oso_core.resources import ResourcesContext
from scheduler.types import (
    FailedResponse,
    GenericMessageQueueService,
    MessageHandlerRegistry,
    SkipResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)


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

    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue"""
        # Implementation for GCP Pub/Sub listening logic goes here

        handler = self.get_queue_listener(queue)

        def callback(raw_message: Message) -> None:
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

            response = safe_run_until_complete(
                self.resources.run(
                    handler.handle_message,
                    additional_inject={
                        "message": message,
                    },
                )
            )
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

        subscriber = SubscriberClient()
        subscription_path = subscriber.subscription_path(self.project_id, queue)

        streaming_pull_future = subscriber.subscribe(
            subscription_path, callback=callback
        )
        logger.info(f"Listening for messages on {subscription_path}...")

        with subscriber:
            try:
                streaming_pull_future.result()
            except Exception as e:
                logger.error(
                    f"Listening for messages on {subscription_path} threw an exception: {e}."
                )
                streaming_pull_future.cancel()

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
