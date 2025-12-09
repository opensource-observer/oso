import logging
import os

from asyncworker.handlers.data_model import DataModelRunRequestHandler
from asyncworker.impl.pubsub import GCPPubSubMessageQueueService
from asyncworker.resources import default_resource_registry
from asyncworker.types import GenericMessageQueueService, MessageQueueHandlerRegistry
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from google.pubsub_v1.types import Encoding, Schema
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, CliApp, CliPositionalArg, SettingsConfigDict

logger = logging.getLogger(__name__)

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../../"))
PROTOBUF_DIR = os.path.join(REPO_DIR, "lib/protobufs/definitions")


class CommonSettings(BaseSettings):
    """Common options for async worker commands"""

    model_config = SettingsConfigDict(env_prefix="asyncworker_")

    k8s_enabled: bool = Field(
        default=False,
        description="Whether Kubernetes is enabled for resource management",
    )
    trino_remote_url: str = "http://localhost:8080"
    trino_k8s_namespace: str = ""
    trino_k8s_service_name: str = ""
    trino_k8s_coordinator_deployment_name: str = ""
    trino_k8s_worker_deployment_name: str = ""
    trino_connect_timeout: int = 240
    k8s_use_port_forward: bool = Field(
        default=False,
        description="Whether to use port forwarding when connecting to k8s services",
    )

    gcp_project_id: str = Field(description="GCP Project ID")
    gcp_bigquery_enabled: bool = Field(
        default=False,
        description="Whether GCP BigQuery is enabled for UDM storage",
    )
    emulator_enabled: bool = Field(
        default=False,
        description="Whether to use the GCP Pub/Sub emulator",
    )

    local_duckdb_path: str = Field(
        default="",
        description="Path to the local DuckDB database file",
    )

    @model_validator(mode="after")
    def handle_generated_config(self):
        if not self.local_duckdb_path:
            self.local_duckdb_path = os.path.join(
                os.getcwd(),
                "duckdb.db",
            )
        return self

    def get_message_queue_service(self) -> GenericMessageQueueService:
        # In the future we'd be able to select different implementations here
        registry = MessageQueueHandlerRegistry()
        registry.register(DataModelRunRequestHandler())

        resources_registry = default_resource_registry()

        return GCPPubSubMessageQueueService(
            project_id=self.gcp_project_id,
            resources=resources_registry,
            registry=registry,  # In real usage, we'd populate this registry
        )


class Run(CommonSettings):
    """Subcommand to run the async worker"""

    queue: CliPositionalArg[str] = Field(description="The name of the queue to process")

    async def cli_cmd(self) -> None:
        # Listen on the given queue
        message_queue_service = self.get_message_queue_service()

        await message_queue_service.run_loop(self.queue)


def ensure_topic_subscription(
    *,
    project_id: str,
    topic_id: str,
    subscription_id: str,
    schema_id: str,
    pb_file_path: str,
    emulator_enabled: bool,
) -> None:
    with open(pb_file_path, "r") as f:
        pb_source = f.read()

    # Create Schema
    schema_client = pubsub_v1.SchemaServiceClient()
    schema_path = schema_client.schema_path(project_id, schema_id)
    parent = f"projects/{project_id}"

    if not emulator_enabled:
        try:
            schema_client.create_schema(
                request={
                    "parent": parent,
                    "schema_id": schema_id,
                    "schema": {
                        "name": schema_path,
                        "type_": Schema.Type.PROTOCOL_BUFFER,
                        "definition": pb_source,
                    },
                }
            )
            logger.info(f"Schema {schema_id} created.")
        except AlreadyExists:
            logger.info(f"Schema {schema_id} already exists.")

    # Create Topic
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    try:
        request: dict = {
            "name": topic_path,
        }
        if not emulator_enabled:
            request["schema_settings"] = {
                "schema": schema_path,
                "encoding": Encoding.BINARY,
            }
        publisher.create_topic(request=request)
        logger.info(f"Topic {topic_id} created.")
    except AlreadyExists:
        logger.info(f"Topic {topic_id} already exists.")

    # Create Subscription
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    try:
        subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
            }
        )
        logger.info(f"Subscription {subscription_id} created.")
    except AlreadyExists:
        logger.info(f"Subscription {subscription_id} already exists.")


class Initialize(CommonSettings):
    """Idempotently initializes the gcp pub/sub topics and subscriptions"""

    async def cli_cmd(self) -> None:
        ensure_topic_subscription(
            project_id=self.gcp_project_id,
            topic_id="data_model_run_requests",
            subscription_id="data_model_run_requests",
            schema_id="data_model_run_request_schema",
            pb_file_path=os.path.join(PROTOBUF_DIR, "data-model.proto"),
            emulator_enabled=self.emulator_enabled,
        )


class Testing(CommonSettings):
    """Subcommand to run tests for the async worker"""

    async def cli_cmd(self) -> None:
        print("Running async worker tests...")
        # Here you would implement actual test running logic
        CliApp.run_subcommand(self)
