import logging

from oso_core.logging.decorators import time_function
from oso_dagster.factories.common import ResourcesContext

from .common import DefinitionsLoaderResponse, dagster_definitions

logger = logging.getLogger(__name__)


@dagster_definitions(name="sqlmesh")
@time_function(logger, override_name="sqlmesh_definitions")
def sqlmesh_definitions(
    resources: ResourcesContext,
) -> DefinitionsLoaderResponse:
    """This is the "legacy" definitions for oso_dagster. It is currently being
    decomposed to smaller sets of code locations.

    Imports are done here to attempt to get a notion of timing for import
    loading.
    """
    from .. import assets
    from ..factories import load_all_assets_from_package

    asset_factories = load_all_assets_from_package(
        assets,
        resources,
        include_module_tags={
            "code_location": "sqlmesh",
        },
    )

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
    )
