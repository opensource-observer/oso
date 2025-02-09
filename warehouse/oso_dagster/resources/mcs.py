"""
Metrics Calculation Service (MCS) resource for Dagster.

This resource is used to interact with the Metrics Calculation Service (MCS)
that is used with sqlmesh to compute metrics.

Two implementations are provided:

- MCSK8sResource: interacts with an MCS deployed on Kubernetes
- MCSRemoteResource: interacts with an MCS deployed independently from dagster
  (intended for testing)
"""

import logging
import typing as t
from contextlib import asynccontextmanager

from dagster import ConfigurableResource, ResourceDependency
from pydantic import Field

from ..utils.http import wait_for_ok_async
from .kube import K8sResource

logger = logging.getLogger(__name__)


class MCSResource(ConfigurableResource):
    """Metrics calculation service resource"""

    @asynccontextmanager
    def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        """Ensure the MCS is available"""
        raise NotImplementedError(
            "ensure_available not implemented on the base MCSResource"
        )


class MCSK8sResource(MCSResource):
    k8s: ResourceDependency[K8sResource]

    service_name: str = Field(
        default="mcs",
        description="MCS service name",
    )

    service_port_name: str = Field(
        default="http",
        description="Trino service port",
    )

    deployment_name: str = Field(
        default="mcs",
        description="MCS deployment name",
    )

    namespace: str = Field(
        default="default",
        description="MCS namespace",
    )

    connect_timeout: int = Field(
        default=240,
        description="Timeout in seconds for waiting for the service to be online",
    )

    use_port_forward: bool = Field(
        default=False,
        description="Use port forward to connect to mcs - should only be used for testing",
    )

    @asynccontextmanager
    async def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        """Ensures that the mcs is deployed and available"""
        async with self.k8s.deployment_context(
            name=self.deployment_name,
            namespace=self.namespace,
            min_replicas=1,
            log_override=log_override,
        ):
            # Check that the service is online
            async with self.k8s.get_service_connection(
                self.service_name,
                self.namespace,
                self.service_port_name,
                use_port_forward=self.use_port_forward,
            ) as (host, port):
                # Wait for the status endpoint to return 200
                await wait_for_ok_async(
                    f"http://{host}:{port}/status", timeout=self.connect_timeout
                )

                yield


class MCSRemoteResource(MCSResource):
    """Resource for interacting with a remote MCS"""

    base_url: str = Field(
        default="http://localhost:8080",
        description="URL for the remote MCS",
    )

    connect_timeout: int = Field(
        default=240,
        description="Timeout in seconds for waiting for the service to be online",
    )

    @asynccontextmanager
    async def ensure_available(self, log_override: t.Optional[logging.Logger] = None):
        """Ensures that the remote mcs is available"""
        await wait_for_ok_async(f"{self.url}/status", timeout=self.connect_timeout)
        yield
