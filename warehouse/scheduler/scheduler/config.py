import asyncio
import os
import typing as t
import uuid

import httpx
import structlog
from aioprometheus.service import Service
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

    model_config = SettingsConfigDict(
        env_prefix="scheduler_",
        env_nested_delimiter="__",
    )

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

    consumer_trino_remote_url: str = "http://localhost:8080"
    consumer_trino_k8s_namespace: str = ""
    consumer_trino_k8s_service_name: str = ""
    consumer_trino_k8s_coordinator_deployment_name: str = ""
    consumer_trino_k8s_worker_deployment_name: str = ""
    consumer_trino_connect_timeout: int = 240

    redis_host: t.Optional[str] = None
    redis_port: int = 6379
    redis_ttl_seconds: int = 3600

    local_heartbeat_path: str = ""

    k8s_use_port_forward: bool = Field(
        default=False,
        description="Whether to use port forwarding when connecting to k8s services",
    )

    gcp_project_id: str = Field(description="GCP Project ID")
    query_bucket: str = Field(
        default="oso-async-query",
        description="GCS bucket for storing query results",
    )
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

    local_duckdb_dir_path: str = Field(
        default="",
        description="Path to the a directory to store local DuckDB files",
    )

    oso_api_url: str = Field(
        description="URL for the OSO API GraphQL endpoint",
    )
    oso_system_api_key: str = Field(
        default="",
        description="API key for authenticating with the OSO system",
    )

    upload_filesystem_bucket_url: str = Field(
        default="s3://static-model-files",
        description="The filesystem bucket URL for uploading static model files",
    )

    upload_filesystem_access_key_id: str = Field(
        default="",
        description="The access key ID for the upload filesystem",
    )

    upload_filesystem_secret_access_key: str = Field(
        default="",
        description="The secret access key for the upload filesystem",
    )
    upload_filesystem_endpoint_url: str = Field(
        default="",
        description="The endpoint URL for the upload filesystem",
    )
    warehouse_shared_catalog_name: str = Field(
        default="user_shared",
        description="The name of the shared catalog in the data warehouse",
    )

    marimo_url: str = Field(
        default="https://marimo.oso.xyz",
        description="The base URL for the Marimo service",
    )

    enable_run_logs_upload: bool = Field(
        default=False,
        description="Whether to upload run logs to GCS",
    )

    run_logs_gcs_bucket: str = Field(
        default="oso-run-logs",
        description="GCS bucket for storing run logs",
    )

    posthog_api_key: str = Field(
        default="",
        description="API key for PostHog analytics",
    )

    posthog_host: str = Field(
        default="https://us.i.posthog.com",
        description="Host URL for PostHog analytics",
    )

    concurrency_lock_ttl_seconds: int = Field(
        default=120,
        description="Time-to-live for concurrency locks in seconds",
    )

    message_handling_timeout_seconds: float = Field(
        default=300,
        description="Timeout for handling messages in seconds",
    )

    message_handling_heartbeat_interval_seconds: float = Field(
        default=15,
        description="Interval for sending heartbeats while handling messages in seconds",
    )
    message_handling_heartbeat_buffer_factor: int = Field(
        default=3,
        description="Buffer factor to multiply the heartbeat interval by to determine the Pub/Sub ack deadline",
    )

    @model_validator(mode="after")
    def handle_generated_config(self):
        if not self.local_duckdb_dir_path:
            self.local_duckdb_dir_path = os.path.join(
                self.local_working_dir,
                ".duckdb_catalogs",
            )
            # Ensure the directory exists
            os.makedirs(self.local_duckdb_dir_path, exist_ok=True)
        if not self.local_heartbeat_path:
            self.local_heartbeat_path = os.path.join(
                self.local_working_dir,
                "heartbeat",
            )
        if os.environ.get("PUBSUB_EMULATOR_HOST"):
            self.emulator_enabled = True
        if self.env == "production":
            self.trino_enabled = True
            self.enable_run_logs_upload = True

            assert self.upload_filesystem_access_key_id != "", (
                "upload_filesystem_access_key_id must be set in production"
            )
            assert self.upload_filesystem_secret_access_key != "", (
                "upload_filesystem_secret_access_key must be set in production"
            )
            assert self.upload_filesystem_endpoint_url != "", (
                "upload_filesystem_endpoint_url must be set in production"
            )

        return self

    @property
    def local_duckdb_path(self) -> str:
        return os.path.join(
            self.local_duckdb_dir_path,
            f"{self.warehouse_shared_catalog_name}.duckdb",
        )


class Run(BaseSettings):
    """Subcommand to run the async worker"""

    queue: CliPositionalArg[str] = Field(description="The name of the queue to process")
    host: str = Field(
        default="localhost",
        description="The host address to bind the worker",
    )
    port: int = Field(
        default=8070,
        description="The port to bind the worker",
    )

    async def cli_cmd(self, context: CliContext) -> None:
        resources_registry = context.get_data_as(
            "resources_registry", ResourcesRegistry
        )
        resources = resources_registry.context()

        # Listen on the given queue
        message_queue_service: GenericMessageQueueService = resources.resolve(
            "message_queue_service"
        )

        prometheus_service = Service()

        await prometheus_service.start(addr=self.host, port=self.port)
        logger.info(f"Prometheus service started at {self.host}:{self.port}")

        await message_queue_service.start(self.queue)

        await prometheus_service.stop()


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


class PublishQueryRunRequest(BaseSettings):
    """Subcommand to publish a QueryRunRequest message"""

    run_id: str = Field(description="The ID of the query run")
    query: str = Field(description="The SQL query to run")
    user: str = Field(description="The user for authentication")

    async def cli_cmd(self, context: CliContext) -> None:
        print(f"Publishing QueryRunRequest with run_id: {self.run_id}")
        resources_registry = context.get_data_as(
            "resources_registry", ResourcesRegistry
        )
        resources = resources_registry.context()

        message_queue_service: GenericMessageQueueService = resources.resolve(
            "message_queue_service"
        )

        from osoprotobufs.query_pb2 import QueryRunRequest

        message = QueryRunRequest(
            run_id=uuid.UUID(self.run_id).bytes,
            query=self.query,
            user=self.user,
        )

        print(f"Message constructed: {message}")

        await message_queue_service.publish_message(
            "query_run_requests",
            message,
        )


class AsyncQueryBatchTest(BaseSettings):
    """Subcommand to that expects the frontend service to be available and calls
    the async query endpoint with many requests."""

    model_config = SettingsConfigDict(env_prefix="scheduler_")

    query: str = Field(
        description="The SQL query to send in each request",
    )
    num_messages: int = Field(
        default=10,
        description="The number of QueryRunRequest messages to publish",
    )
    port: int = Field(
        default=3000,
        description="The port where the frontend service is running",
    )
    host: str = Field(
        default="localhost",
        description="The host where the frontend service is running",
    )
    path: str = Field(
        default="/api/v1/async-sql",
        description="The path for the async query endpoint",
    )
    oso_api_key: str = Field(
        description="The OSO API key for authentication",
    )

    async def cli_cmd(self, context: CliContext) -> None:
        posted_requests: list[t.Coroutine[None, None, httpx.Response]] = []
        async with httpx.AsyncClient() as client:
            for i in range(self.num_messages):
                query = self.query
                payload = {
                    "query": query,
                }
                url = f"http://{self.host}:{self.port}{self.path}"
                headers = {"Authorization": f"Bearer {self.oso_api_key}"}
                print(url)
                posted_requests.append(client.post(url, json=payload, headers=headers))
            success_count = 0
            failed_count = 0
            for response in await asyncio.gather(*posted_requests):
                if response.status_code >= 200 and response.status_code < 300:
                    success_count += 1
                else:
                    failed_count += 1
                    print(
                        f"Request failed with status {response.status_code}: {response.text}"
                    )
            print(
                f"Batch test completed. Successful requests: {success_count}, Failed requests: {failed_count}"
            )


class Publish(BaseSettings):
    """Subcommand to run the async worker publisher"""

    data_model_run_request: CliSubCommand[PublishDataModelRunRequest]
    query_run_request: CliSubCommand[PublishQueryRunRequest]

    async def cli_cmd(self, context: CliContext) -> None:
        CliApp.run_subcommand(context, self)


class Testing(BaseSettings):
    """Subcommand to run tests for the async worker"""

    publish: CliSubCommand[Publish]
    async_query_batch_test: CliSubCommand[AsyncQueryBatchTest]
    create_system_jwt_secret: CliSubCommand[CreateSystemJWTSecret]

    async def cli_cmd(self, context: CliContext) -> None:
        # Here you would implement actual test running logic
        CliApp.run_subcommand(context, self)
