from dagster import Definitions
from oso_dagster.factories.common import AssetFactoryResponse


def load_definitions_with_asset_factories(
    asset_factories: AssetFactoryResponse, **kwargs
) -> Definitions:
    return Definitions(
        assets=asset_factories.assets,
        jobs=asset_factories.jobs,
        asset_checks=asset_factories.checks,
        sensors=asset_factories.sensors,
        **kwargs,
    )
