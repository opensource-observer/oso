import inspect
import logging
import typing as t
from dataclasses import dataclass

import dagster as dg
from dagster_k8s import k8s_job_executor
from oso_core.logging import setup_module_logging
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import (
    AssetFactoryResponse,
    ResourceFactory,
    ResourcesRegistry,
)

from .resources import default_resource_registry


@dataclass(kw_only=True)
class DefinitionsLoaderResponse:
    asset_factory_response: AssetFactoryResponse
    kwargs: dict[str, t.Any] | None = None


type DefinitionsLoaderFunc = t.Callable[..., DefinitionsLoaderResponse]


class DefinitionsLoader:
    """Wraps common patterns for loading OSO dagster definitions"""

    def __init__(self, func: DefinitionsLoaderFunc):
        self._func = func

    def load(self, resource_registry: ResourcesRegistry) -> dg.Definitions:
        """Load definitions using the provided resource registry."""
        context = resource_registry.context()
        response = context.run(self._func)

        global_config: DagsterConfig = context.resolve("global_config")

        if not isinstance(response, DefinitionsLoaderResponse):
            raise ValueError(
                "The loader function must return a DefinitionLoaderResponse typed dictionary."
            )

        asset_factory_response = response.asset_factory_response
        response_kwargs = response.kwargs or {}

        # Automatically wire the necessary resources based on all of the assets'
        # requirements
        resources_dict: dict[str, t.Any] = {}
        for asset in asset_factory_response.assets:
            if isinstance(asset, dg.AssetsDefinition):
                for resource_key in asset.required_resource_keys:
                    if resource_key not in resources_dict:
                        resources_dict[resource_key] = context.resolve(resource_key)

        if global_config.k8s_executor_enabled:
            response_kwargs["executor"] = k8s_job_executor.configured(
                {
                    "max_concurrent": 10,
                }
            )

        return dg.Definitions(
            assets=asset_factory_response.assets,
            jobs=asset_factory_response.jobs,
            asset_checks=asset_factory_response.checks,
            sensors=asset_factory_response.sensors,
            resources=resources_dict,
            loggers={
                "console": dg.json_console_logger,
            },
            **response_kwargs,
        )


def run_with_default_resources[T](
    func: t.Callable[..., T],
    override_resources: list[ResourceFactory] | None = None,
    **kwargs: t.Any,
) -> T:
    """Run a function with the default resources."""
    registry = default_resource_registry()

    if override_resources:
        registry = registry.clone()
        for factory in override_resources:
            registry.add(factory, override=True)

    resources = registry.context()

    return resources.run(func, **kwargs)


def dagster_definitions(name: str):
    """Magic decorator that turns any function into a `DefinitionsLoader`.
    It automatically wires the resources, loads the `.env` files, and wires
    logging for some default loggers.

    Args:
        name: The name of the definitions.
    """

    from dotenv import load_dotenv

    load_dotenv()

    def _decorator(f: t.Callable[..., DefinitionsLoaderResponse]) -> dg.Definitions:
        caller_module = inspect.getmodule(inspect.stack()[1][0])

        if not caller_module:
            raise ValueError(
                "Could not determine caller module for dagster_definitions"
            )

        caller_module_name = caller_module.__name__
        setup_module_logging("oso_dagster")
        setup_module_logging("dagster_sqlmesh")

        caller_logger = logging.getLogger(caller_module_name)
        caller_logger.info(
            f"Loading dagster definitions for {name} in {caller_module_name}",
            extra={
                "event_type": "dagster_definitions",
                "definitions_module": caller_module_name,
                "dagster_definition": name,
            },
        )

        resource_registry = default_resource_registry()

        loader = DefinitionsLoader(f)

        return loader.load(resource_registry)

    return _decorator
