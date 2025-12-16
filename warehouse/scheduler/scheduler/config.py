import os
import typing as t

import structlog
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
from scheduler.types import GenericMessageQueueService, MessageHandlerRegistry

logger = structlog.get_logger(__name__)

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

    redis_host: t.Optional[str] = None
    redis_port: int = 6379
    redis_ttl_seconds: int = 3600

    local_heartbeat_path: str = ""

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

    local_working_dir: str = Field(
        default=os.path.join(os.getcwd(), ".scheduler_workdir"),
        description="Local working directory for the scheduler",
    )

    local_duckdb_path: str = Field(
        default="",
        description="Path to the local DuckDB database file",
    )
    oso_api_url: str = Field(
        description="URL for the OSO API GraphQL endpoint",
    )
    oso_system_api_key: str = Field(
        default="",
        description="API key for authenticating with the OSO system",
    )

    @model_validator(mode="after")
    def handle_generated_config(self):
        if not self.local_duckdb_path:
            self.local_duckdb_path = os.path.join(
                self.local_working_dir,
                "duckdb.db",
            )
        if not self.local_heartbeat_path:
            self.local_heartbeat_path = os.path.join(
                self.local_working_dir,
                "heartbeat",
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


class CreateSystemJWTSecret(BaseSettings):
    """Subcommand to create a system JWT secret in the OSO system"""

    oso_jwt_secret: str = Field(
        description="The JWT secret to set in the OSO system",
    )

    async def cli_cmd(self, context: CliContext) -> None:
        import jwt

        payload = {
            "iss": "opensource-observer",
            "aud": "opensource-observer",
            "source": "whatgoeshere",
        }
        token = jwt.encode(payload, self.oso_jwt_secret, algorithm="HS256")
        print(f"Generated JWT Token:\n   {token}")


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

        resources_registry = context.get_data_as(
            "resources_registry", ResourcesRegistry
        )
        resources = resources_registry.context()

        message_handler_registry: MessageHandlerRegistry = resources.resolve(
            "message_handler_registry"
        )

        for topic, handler in message_handler_registry:
            logger.info(f"Initializing topic and subscription for {topic}")
            ensure_topic_subscription(
                project_id=common_settings.gcp_project_id,
                topic_id=topic,
                subscription_id=topic,
                schema_id=f"{topic}_schema",
                pb_file_path=os.path.join(PROTOBUF_DIR, handler.schema_file_name),
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
    create_system_jwt_secret: CliSubCommand[CreateSystemJWTSecret]

    async def cli_cmd(self, context: CliContext) -> None:
        # Here you would implement actual test running logic
        CliApp.run_subcommand(context, self)
