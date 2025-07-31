import typing as t

from dagster import Definitions, json_console_logger
from oso_dagster.factories.common import AssetFactoryResponse

from .resources import default_resource_registry


def load_definitions_with_asset_factories(
    asset_factories: AssetFactoryResponse, **kwargs
) -> Definitions:
    return Definitions(
        assets=asset_factories.assets,
        jobs=asset_factories.jobs,
        asset_checks=asset_factories.checks,
        sensors=asset_factories.sensors,
        loggers={
            "console": json_console_logger,
        },
        **kwargs,
    )


def run_with_default_resources[T](
    func: t.Callable[..., T],
    **kwargs: t.Any,
) -> T:
    """Run a function with the default resources."""
    registry = default_resource_registry()
    resources = registry.context()

    return resources.run(func, **kwargs)
