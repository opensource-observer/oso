import logging

from oso_core.logging.decorators import time_function
from oso_dagster.factories.common import ResourcesContext

from .common import DefinitionsLoaderResponse, dagster_definitions

logger = logging.getLogger(__name__)


@dagster_definitions(name="default")
@time_function(logger, override_name="default_definitions")
def default_definitions(
    resources: ResourcesContext,
) -> DefinitionsLoaderResponse:
    """This is the "default" definitions for oso_dagster. Anything in the
    `oso_dagster.assets.default` package is loaded by this code location.
    """
    from ..assets import default as default_assets
    from ..factories import load_all_assets_from_package

    asset_factories = load_all_assets_from_package(
        default_assets,
        resources,
    )

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
    )
