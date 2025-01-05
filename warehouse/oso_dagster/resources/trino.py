import logging
import typing as t
from contextlib import asynccontextmanager

import trino
from dagster import ConfigurableResource, ResourceDependency
from pydantic import Field

from ..utils.asynctools import multiple_async_contexts
from ..utils.http import wait_for_ok_async
from .kube import K8sResource

module_logger = logging.getLogger(__name__)


class TrinoResource(ConfigurableResource):
    """Base Trino resource"""

    def get_client(self):
        raise NotImplementedError(
            "get_client not implemented on the base TrinoResource"
        )

    @asynccontextmanager
    def async_get_client(self, log_override: t.Optional[logging.Logger] = None):
        raise NotImplementedError(
            "get_client not implemented on the base TrinoResource"
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

    @asynccontextmanager
    async def get_client(self, log_override: t.Optional[logging.Logger] = None):
        logger = log_override or module_logger
        # Bring both the coordinator and worker online if they aren't already

        async with self.ensure_available(log_override=log_override):
            # Wait for the status endpoint to return 200
            host, port = await self.k8s.get_service_connection(
                self.service_name, self.namespace, self.service_port_name
            )
            logger.info(f"Wait for trino to be online at http://{host}:{port}/")

            await wait_for_ok_async(
                f"http://{host}:{port}/", timeout=self.deploy_timeout
            )
            yield trino.dbapi.connect(
                host=host,
                port=port,
                user=self.user,
                catalog=self.catalog,
                schema=self.connection_schema,
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
            host, port = await self.k8s.get_service_connection(
                self.service_name, self.namespace, self.service_port_name
            )
            url = f"http://{host}:{port}/"

            logger.info(f"Wait for trino to be online at {url}")
            # Wait for the status endpoint to return 200
            await wait_for_ok_async(url, timeout=self.connect_timeout)

            yield


class TrinoRemoteResource(TrinoResource):
    """Remote trino resource assumes that trino is already deployed somewhere"""

    url: str = Field(
        default="http://localhost:8080",
        description="Trino url",
    )

    @asynccontextmanager
    async def get_client(self, log_override: t.Optional[logging.Logger] = None):
        logger = log_override or module_logger
        async with self.ensure_available(log_override=log_override):
            await wait_for_ok_async(self.url, timeout=self.connect_timeout)

            logger.info("Connecting to trino")
            yield trino.dbapi.connect(
                host=self.url,
                user=self.user,
                catalog="hive",
                schema="default",
            )

    @asynccontextmanager
    async def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        logger = log_override or module_logger

        logger.info("Wait for trino to be online")
        await wait_for_ok_async(self.url, timeout=self.connect_timeout)

        yield
