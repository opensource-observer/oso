import logging

from oso_core.logging.decorators import time_function
from oso_dagster.factories.common import ResourcesContext

from .common import DefinitionsLoaderResponse, dagster_definitions

logger = logging.getLogger(__name__)


@dagster_definitions(name="dynamic")
@time_function(logger, override_name="dynamic_definitions")
def dynamic_definitions(
    resources: ResourcesContext,
) -> DefinitionsLoaderResponse:
    """This is the dynamic definitions for oso_dagster."""
    from ..factories import load_all_assets_from_packages

    asset_factories = load_all_assets_from_packages(
        ["oso_dagster.assets.dynamic"],
        resources,
    )

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
    )
