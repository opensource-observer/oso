import logging
import os
import typing as t

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from google.pubsub_v1.types import Encoding, Schema
from oso_core.cli.utils import CliApp, CliContext
from oso_core.resources import ResourcesRegistry
from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
    SettingsConfigDict,
)
from scheduler.types import GenericMessageQueueService

logger = logging.getLogger(__name__)

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../../"))
PROTOBUF_DIR = os.path.join(REPO_DIR, "lib/osoprotobufs/definitions")


class CommonSettings(BaseSettings):
    """Common options for async worker commands"""

    model_config = SettingsConfigDict(env_prefix="scheduler_")

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
    emulator_enabled: bool = Field(
        default=False,
        description="Whether to use the GCP Pub/Sub emulator",
    )

    env: t.Literal["dev", "production"] = "dev"

    trino_enabled: bool = False

    local_duckdb_path: str = Field(
        default="",
        description="Path to the local DuckDB database file",
    )
    oso_api_url: str = Field(
        description="URL for the OSO API GraphQL endpoint",
    )

    @model_validator(mode="after")
    def handle_generated_config(self):
        if not self.local_duckdb_path:
            self.local_duckdb_path = os.path.join(
                os.getcwd(),
                "duckdb.db",
            )
        if os.environ.get("PUBSUB_EMULATOR_HOST"):
            self.emulator_enabled = True
        if self.env == "production":
            self.trino_enabled = True
        return self


class Run(BaseSettings):
    """Subcommand to run the async worker"""

    queue: CliPositionalArg[str] = Field(description="The name of the queue to process")

    async def cli_cmd(self, context: CliContext) -> None:
        resources_registry = context.get_data_as(
            "resources_registry", ResourcesRegistry
        )
        resources = resources_registry.context()

        # Listen on the given queue
        message_queue_service: GenericMessageQueueService = resources.resolve(
            "message_queue_service"
        )

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


class Initialize(BaseSettings):
    """Idempotently initializes the gcp pub/sub topics and subscriptions"""

    async def cli_cmd(self, context: CliContext) -> None:
        common_settings = context.get_data_as("common_settings", CommonSettings)

        ensure_topic_subscription(
            project_id=common_settings.gcp_project_id,
            topic_id="data_model_run_requests",
            subscription_id="data_model_run_requests",
            schema_id="data_model_run_request_schema",
            pb_file_path=os.path.join(PROTOBUF_DIR, "data-model.proto"),
            emulator_enabled=common_settings.emulator_enabled,
        )


class PublishDataModelRunRequest(BaseSettings):
    """Subcommand to publish a DataModelRunRequest message"""

    run_id: str = Field(description="The ID of the data model run")
    dataset_id: str = Field(description="The ID of the dataset")

    async def cli_cmd(self, context: CliContext) -> None:
        resources_registry = context.get_data_as(
            "resources_registry", ResourcesRegistry
        )
        resources = resources_registry.context()

        message_queue_service: GenericMessageQueueService = resources.resolve(
            "message_queue_service"
        )

        from osoprotobufs.data_model_pb2 import DataModelRunRequest

        message = DataModelRunRequest(
            run_id=self.run_id.encode("utf-8"),
            dataset_id=self.dataset_id,
        )

        await message_queue_service.publish_message(
            "data_model_run_requests",
            message,
        )


class Publish(BaseSettings):
    """Subcommand to run the async worker publisher"""

    data_model_run_request: CliSubCommand[PublishDataModelRunRequest]

    async def cli_cmd(self, context: CliContext) -> None:
        CliApp.run_subcommand(context, self)


class Testing(BaseSettings):
    """Subcommand to run tests for the async worker"""

    publish: CliSubCommand[Publish]

    async def cli_cmd(self, context: CliContext) -> None:
        # Here you would implement actual test running logic
        CliApp.run_subcommand(context, self)
