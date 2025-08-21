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
    """This is the sqlmesh definitions for oso_dagster.

    sqlmesh is kept separately because it takes more time to load and we want to
    make it easier to develop things locally.
    """
    from ..assets import sqlmesh as sqlmesh_assets
    from ..factories import load_all_assets_from_package

    asset_factories = load_all_assets_from_package(
        sqlmesh_assets,
        resources,
    )

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
    )
