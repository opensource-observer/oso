"""
The `ops` code definitions. These are dagster definitions that run outside of
the assets. Things like schedules and sensors that are not tied to a specific
asset or loosely tied based on some programmatic conditions.
"""

import logging

from oso_core.logging.decorators import time_function
from oso_dagster.utils.alerts import AlertManager

from ..config import DagsterConfig
from .common import DefinitionsLoaderResponse, dagster_definitions

logger = logging.getLogger(__name__)


@dagster_definitions(name="ops")
@time_function(logger, override_name="ops_definitions")
def ops_definitions(
    global_config: DagsterConfig,
    alert_manager: AlertManager,
) -> DefinitionsLoaderResponse:
    """This is the "legacy" definitions for oso_dagster. It is currently being
    decomposed to smaller sets of code locations.

    Imports are done here to attempt to get a notion of timing for import
    loading.
    """
    from ..factories.alerts import setup_alert_sensors
    from ..schedules import get_partitioned_schedules, schedules
    from ..utils import setup_chunked_state_cleanup_sensor

    alerts = setup_alert_sensors(
        global_config.alerts_base_url,
        alert_manager,
        False,
    )

    asset_factories = alerts

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
