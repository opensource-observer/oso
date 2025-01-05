"""
Kubernetes resource for Dagster.

This can be used to ensure deployments are up and running for the assets that
might need certain kubernetes resources.
"""

import inspect
import logging
import os
import typing as t
from contextlib import asynccontextmanager

from dagster import ConfigurableResource, ResourceDependency
from kr8s.objects import Deployment, Service
from pydantic import Field

from ..utils import SecretResolver

logger = logging.getLogger(__name__)


class K8sResource(ConfigurableResource):
    """Resource for interacting with kubernetes. This is more of a convenience
    utility. However, we encapsulate interactions with k8s resources here to
    make it easier to mock any k8s interactions in dagster assets if necessary.
    """

    secrets: ResourceDependency[SecretResolver]

    secret_group_name: str

    service_name: str = Field(
        default="trino",
        description="Trino service name",
    )

    deployment_name: str = Field(
        default="trino",
        description="Trino deployment name",
    )

    port: int = Field(
        default=8080,
        description="Trino port",
    )

    namespace: str = Field(
        default="default",
        description="Trino k8s namespace",
    )

    @asynccontextmanager
    async def deployment_context(
        self,
        name: str,
        namespace: str,
        min_replicas: int = 1,
        log_override: t.Optional[logging.Logger] = None,
        always_scale_down: bool = False,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""

        starting_replicas, _ = await self.ensure_deployment_scale_up(
            name,
            namespace,
            min_replicas,
        )

        try:
            yield
        finally:
            if always_scale_down:
                await self.ensure_deployment_scale_down(
                    name,
                    namespace,
                    0,
                    log_override=log_override,
                )
            else:
                await self.ensure_deployment_scale_down(
                    name,
                    namespace,
                    starting_replicas,
                    log_override=log_override,
                )

    async def ensure_deployment_scale_up(
        self,
        name: str,
        namespace: str,
        min_replicas: int = 1,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""
        log = log_override or logger
        deployment = await Deployment.get(name=name, namespace=namespace)

        starting_replicas = deployment.replicas

        if starting_replicas < min_replicas:
            log.info(f"Scaling up {name} in {namespace}")
            result = deployment.scale(min_replicas)
            if inspect.isawaitable(result):
                await result
        return (starting_replicas, deployment.replicas)

    async def ensure_deployment_scale_down(
        self,
        name: str,
        namespace: str,
        max_replicas: int = 0,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""
        log = log_override or logger
        deployment = await Deployment.get(name=name, namespace=namespace)

        starting_replicas = deployment.replicas

        if starting_replicas > max_replicas:
            log.info(f"Scaling down {name} in {namespace}")
            result = deployment.scale(max_replicas)
            if inspect.isawaitable(result):
                await result
        return (starting_replicas, deployment.replicas)

    async def get_service_connection(self, name: str, namespace: str, port_name: str):
        """Returns the host:port url to the service."""

        if not os.environ.get("KUBERNETES_SERVICE_HOST"):
            raise Exception("Not running in a k8s cluster")

        service = await Service.get(name=name, namespace=namespace)
        ports = t.cast(t.List[dict], service.spec.ports)
        ports_lookup = {port["name"]: port["port"] for port in ports}
        return f"{service.name}.{service.namespace}.svc.cluster.local", int(
            ports_lookup[port_name]
        )
