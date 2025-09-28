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

    This is kept separate _specifically_ to help with development of assets that
    are not sqlmesh. sqlmesh assets take a long time to load. In production this
    code location is not used because of some existing issues with dagster
    schedules and multiple code locations. Additionally, on production we are
    able to build the sqlmesh assets cache in the docker container of every
    deployment so loading takes significantly less time.
    """
    from ..factories import load_all_assets_from_packages

    asset_factories = load_all_assets_from_packages(
        ["oso_dagster.assets.sqlmesh"],
        resources,
    )

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
    )
