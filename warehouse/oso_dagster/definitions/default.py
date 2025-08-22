import logging

from oso_core.logging.decorators import time_function
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import ResourcesContext
from oso_dagster.utils.alerts import AlertManager

from .common import DefinitionsLoaderResponse, dagster_definitions

logger = logging.getLogger(__name__)


@dagster_definitions(name="default")
@time_function(logger, override_name="default_definitions")
def default_definitions(
    resources: ResourcesContext,
    global_config: DagsterConfig,
    alert_manager: AlertManager,
) -> DefinitionsLoaderResponse:
    """This is the "default" definitions for oso_dagster. Anything in the
    `oso_dagster.assets.default` package is loaded by this code location.
    """
    from ..factories import load_all_assets_from_packages
    from ..factories.alerts import setup_alert_sensors
    from ..schedules import get_partitioned_schedules, schedules
    from ..utils import setup_chunked_state_cleanup_sensor

    packages = ["oso_dagster.assets.default"]
    # Append the sqlmesh package if it's enabled. This is automatically done on
    # production. We keep this separate for local development because sqlmesh
    # takes a long time to load. If developing locally, it's easiest to use the
    # separate code location.
    if global_config.sqlmesh_assets_on_default_code_location_enabled:
        packages.append("oso_dagster.assets.sqlmesh")

    asset_factories = load_all_assets_from_packages(
        packages,
        resources,
    )

    alerts = setup_alert_sensors(
        global_config.alerts_base_url,
        alert_manager,
        False,
    )

    asset_factories = asset_factories + alerts

    chunked_state_cleanup_sensor = setup_chunked_state_cleanup_sensor(
        global_config.gcs_bucket,
    )

    asset_factories = asset_factories + chunked_state_cleanup_sensor

    all_schedules = schedules + get_partitioned_schedules(asset_factories)

    return DefinitionsLoaderResponse(
        asset_factory_response=asset_factories,
        kwargs={
            "schedules": all_schedules,
        },
    )
