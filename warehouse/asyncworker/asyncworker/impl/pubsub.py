import asyncio
import logging

from asyncworker.types import GenericMessageQueueService, MessageQueueHandlerRegistry
from google.cloud.pubsub import SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from oso_core.resources import ResourcesRegistry

logger = logging.getLogger(__name__)


class GCPPubSubMessageQueueService(GenericMessageQueueService):
    def __init__(
        self,
        project_id: str,
        resources: ResourcesRegistry,
        registry: MessageQueueHandlerRegistry,
    ) -> None:
        super().__init__(resources, registry)
        self.project_id = project_id

    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue"""
        # Implementation for GCP Pub/Sub listening logic goes here

        loop = asyncio.get_running_loop()

        handler = self.get_queue_listener(queue)

        def callback(raw_message: Message) -> None:
            # Get the message serialization type.
            encoding = raw_message.attributes.get("googclient_schemaencoding")
            # Deserialize the message data accordingly.
            if encoding == "BINARY":
                message = handler.parse_binary_message(raw_message.data)
                logger.debug(f"Received binary message on {queue}: {message}")
            elif encoding == "JSON":
                message = handler.parse_json_message(raw_message.data)
                logger.debug(f"Received JSON message on {queue}: {message}")
            else:
                raw_message.ack()
                return

            resources_context = self.resources.context()

            loop.run_until_complete(
                resources_context.run(
                    handler.handle_message,
                    additional_inject={
                        "message": message,
                    },
                )
            )
            raw_message.ack()

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
