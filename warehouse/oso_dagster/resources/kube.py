"""
Kubernetes resource for Dagster.

This can be used to ensure deployments are up and running for the assets that
might need certain kubernetes resources.
"""

import inspect
import logging
import typing as t
from contextlib import asynccontextmanager

from dagster import ConfigurableResource
from kr8s.asyncio.objects import Deployment, Service

logger = logging.getLogger(__name__)


class K8sResource(ConfigurableResource):
    """Base k8s resource"""

    @asynccontextmanager
    def deployment_context(
        self,
        name: str,
        namespace: str,
        min_replicas: int = 1,
        log_override: t.Optional[logging.Logger] = None,
        always_scale_down: bool = False,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""
        raise NotImplementedError(
            "deployment_context not implemented on the base K8sResource"
        )

    async def ensure_deployment_scale_up(
        self,
        name: str,
        namespace: str,
        min_replicas: int = 1,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""
        raise NotImplementedError(
            "ensure_deployment_scale_up not implemented on the base K8sResource"
        )

    async def ensure_deployment_scale_down(
        self,
        name: str,
        namespace: str,
        max_replicas: int = 0,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """Ensures a deployment is running with at least `min_replicas` replicas."""
        raise NotImplementedError(
            "ensure_deployment_scale_down not implemented on the base K8sResource"
        )

    @asynccontextmanager
    def get_service_connection(
        self, name: str, namespace: str, port_name: str, use_port_forward: bool = False
    ) -> t.AsyncIterator[t.Tuple[str, int]]:
        """Returns the host:port url to the service."""
        raise NotImplementedError(
            "get_service_connection not implemented on the base K8sResource"
        )


class K8sApiResource(ConfigurableResource):
    """Resource for interacting with kubernetes from within a pod. This is more
    of a convenience utility. However, we encapsulate interactions with k8s
    resources here to make it easier to mock any k8s interactions in dagster
    assets if necessary.
    """

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

    @asynccontextmanager
    async def get_service_connection(
        self, name: str, namespace: str, port_name: str, use_port_forward: bool = False
    ):
        """Returns the host:port url to the service."""
        service = t.cast(Service, await Service.get(name=name, namespace=namespace))
        ports = t.cast(t.List[dict], service.spec.ports)
        ports_lookup = {port["name"]: port["port"] for port in ports}
        port = int(ports_lookup[port_name])
        if not use_port_forward:
            yield f"{service.name}.{service.namespace}.svc.cluster.local", port
            return
        else:
            pf = service.portforward(remote_port=port)
            async with pf as local_port:
                yield "localhost", local_port
