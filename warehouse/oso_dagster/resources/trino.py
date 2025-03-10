import logging
import typing as t
from contextlib import asynccontextmanager, contextmanager

import aiotrino
from aiotrino.dbapi import Connection as AsyncConnection
from dagster import ConfigurableResource, ResourceDependency
from metrics_tools.transfer.trino import TrinoExporter
from oso_dagster.resources.storage import TimeOrderedStorageResource
from pydantic import Field
from trino.dbapi import Connection

from ..utils.asynctools import multiple_async_contexts
from ..utils.http import wait_for_ok_async
from .kube import K8sResource

module_logger = logging.getLogger(__name__)


class TrinoResource(ConfigurableResource):
    """Base Trino resource"""

    @contextmanager
    def get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.Iterator[Connection]:
        raise NotImplementedError(
            "get_client not implemented on the base TrinoResource"
        )

    @asynccontextmanager
    def async_get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.AsyncGenerator[AsyncConnection, None]:
        raise NotImplementedError(
            "async_get_client not implemented on the base TrinoResource"
        )

    @asynccontextmanager
    def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        raise NotImplementedError(
            "ensure_available not implemented on the base TrinoResource"
        )


class TrinoK8sResource(TrinoResource):
    """Resource for interacting with Trino deployed on kubernetes. By default
    trino isn't running. The `get_client` context manager on this resource will
    start trino and stop it when the context manager exits.

    Examples:

        To use as a synchronous context:
        .. code-block:: python

            @asset
            def tables(trino: TrinoResource):
                with trino.get_client() as client:
                    client.query(...)

            defs = Definitions(
                assets=[tables], resources={
                    "trino": ClickhouseResource()
                }
            )

        To use as an asynchronous context (this is useful if you have multiple async contexts to use):

        .. code-block:: python

            @asset
            async def tables(trino: TrinoResource):
                async with trino.async_get_client() as client:
                    # Do something with the client (the client is synchronous)
                    client.query(...)

            defs = Definitions(
                assets=[tables], resources={
                    "trino": ClickhouseResource()
                }
            )

    """

    k8s: ResourceDependency[K8sResource]

    user: str = Field(
        default="dagster",
        description="Trino user",
    )

    service_name: str = Field(
        default="trino",
        description="Trino service name",
    )

    service_port_name: str = Field(
        default="http",
        description="Trino service port",
    )

    coordinator_deployment_name: str = Field(
        default="trino-coordinator",
        description="Trino deployment name",
    )

    worker_deployment_name: str = Field(
        default="trino-worker",
        description="Trino worker deployment name",
    )

    namespace: str = Field(
        default="default",
        description="Trino k8s namespace",
    )

    catalog: str = Field(
        default="hive",
        description="Trino catalog",
    )

    connection_schema: str = Field(
        default="default",
        description="Trino schema",
    )

    connect_timeout: int = Field(
        default=240,
        description="Timeout in seconds for waiting for the service to be online",
    )

    use_port_forward: bool = Field(
        default=False,
        description="Use port forward to connect to trino - should only be used for testing",
    )

    @asynccontextmanager
    async def async_get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        # Bring both the coordinator and worker online if they aren't already
        async with self.ensure_available(log_override=log_override):
            # Wait for the status endpoint to return 200
            async with self.k8s.get_service_connection(
                self.service_name,
                self.namespace,
                self.service_port_name,
                use_port_forward=self.use_port_forward,
            ) as (host, port):
                extra_connection_args = {}
                if session_properties:
                    extra_connection_args["session_properties"] = session_properties
                yield aiotrino.dbapi.connect(
                    host=host,
                    port=port,
                    user=self.user,
                    catalog=self.catalog,
                    schema=self.connection_schema,
                    **extra_connection_args,
                )

    @asynccontextmanager
    async def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        """Ensures that the trino is deployed and available"""
        logger = log_override or module_logger
        async with multiple_async_contexts(
            coordinator=self.k8s.deployment_context(
                name=self.coordinator_deployment_name,
                namespace=self.namespace,
                min_replicas=1,
                log_override=log_override,
            ),
            worker=self.k8s.deployment_context(
                name=self.worker_deployment_name,
                namespace=self.namespace,
                min_replicas=1,
                log_override=log_override,
            ),
        ):
            # Check that the service is online
            async with self.k8s.get_service_connection(
                self.service_name,
                self.namespace,
                self.service_port_name,
                use_port_forward=self.use_port_forward,
            ) as (host, port):
                # see: https://github.com/trinodb/trino/issues/14663
                health_check_url = f"http://{host}:{port}/v1/status"

                logger.info(f"Wait for trino to be online at {health_check_url}")
                # Wait for the status endpoint to return 200
                # await wait_for_ok_async(health_check_url, timeout=self.connect_timeout)
                yield


class TrinoRemoteResource(TrinoResource):
    """Remote trino resource assumes that trino is already deployed somewhere"""

    url: str = Field(
        default="http://localhost:8080",
        description="Trino url",
    )

    @asynccontextmanager
    async def async_get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        async with self.ensure_available(log_override=log_override):
            yield aiotrino.dbapi.connect(
                host=self.url,
                user=self.user,
                catalog="hive",
                schema="default",
            )

    @asynccontextmanager
    async def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        logger = log_override or module_logger

        logger.info("Wait for trino to be online")
        health_check_url = f"{self.url}/v1/status"
        await wait_for_ok_async(health_check_url, timeout=self.connect_timeout)

        yield


class TrinoExporterResource(ConfigurableResource):
    trino: ResourceDependency[TrinoResource]

    time_ordered_storage: ResourceDependency[TimeOrderedStorageResource]

    hive_catalog: str = Field(
        default="source",
        description="Hive catalog used for export",
    )

    hive_schema: str = Field(
        default="export",
        description="Hive schema used for export",
    )

    @asynccontextmanager
    async def get_exporter(
        self, export_prefix: str, log_override: t.Optional[logging.Logger] = None
    ) -> t.AsyncGenerator[TrinoExporter, None]:
        async with self.time_ordered_storage.get(export_prefix) as storage:
            async with self.trino.async_get_client(
                log_override=log_override
            ) as connection:
                yield TrinoExporter(
                    hive_catalog=self.hive_catalog,
                    hive_schema=self.hive_schema,
                    time_ordered_storage=storage,
                    connection=connection,
                    log_override=log_override,
                )
