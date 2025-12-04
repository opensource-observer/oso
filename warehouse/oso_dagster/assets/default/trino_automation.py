import dagster as dg
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import (
    AssetFactoryResponse,
    early_resources_asset_factory,
)
from oso_dagster.resources.heartbeat import HeartBeatResource
from oso_dagster.resources.trino import TrinoResource

# This configuration ensures that we use one of the persistent node pools and
# have a smaller resource request for the trino automation pod. It's doing
# simple things and kubernetes doesn't show it being very resource intensive.
TRINO_AUTOMATION_POD_CONFIG = {
    "dagster-k8s/config": {
        "merge_behavior": "SHALLOW",
        "container_config": {
            "resources": {
                "requests": {
                    "cpu": "50m",
                    "memory": "256Mi",
                },
                "limits": {
                    "memory": "1024Mi",
                },
            },
        },
        "pod_spec_config": {
            "node_selector": {
                "pool_type": "persistent",
            },
            "tolerations": [
                {
                    "key": "pool_type",
                    "operator": "Equal",
                    "value": "persistent",
                    "effect": "NoSchedule",
                }
            ],
        },
    },
}


@early_resources_asset_factory()
def trino_automation_assets() -> AssetFactoryResponse:
    # Define a job that checks the heartbeat of "producer_trino". If the
    # heartbeat is older than 30 minutes, we scale trino down to zero.
    @dg.op
    async def trino_heartbeat_checker(
        context: dg.OpExecutionContext,
        global_config: dg.ResourceParam[DagsterConfig],
        trino: dg.ResourceParam[TrinoResource],
        heartbeat: dg.ResourceParam[HeartBeatResource],
    ) -> None:
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)

        last_heartbeat = await heartbeat.get_last_heartbeat_for("producer_trino")
        if last_heartbeat is None:
            context.log.info(
                "No heartbeat found for sqlmesh now ensuring trino shutdown."
            )
            last_heartbeat = now - timedelta(
                minutes=global_config.sqlmesh_trino_ttl_minutes + 1
            )

        # Only scale down trino if we're in a k8s environment
        if not global_config.k8s_enabled:
            return

        if now - last_heartbeat > timedelta(
            minutes=global_config.sqlmesh_trino_ttl_minutes
        ):
            context.log.info(
                f"No heartbeat detected for sqlmesh in the last {global_config.sqlmesh_trino_ttl_minutes} minutes. Ensuring that producer trino is scaled down."
            )
            await trino.ensure_shutdown()
        else:
            context.log.info("Heartbeat detected for sqlmesh. No action needed.")

    # Use the in-process executor for the heartbeat monitor job to avoid
    # the overhead of spinning up a new k8s pod in addition to the run launcher
    @dg.job(executor_def=dg.in_process_executor, tags=TRINO_AUTOMATION_POD_CONFIG)
    def trino_heartbeat_monitor_job():
        trino_heartbeat_checker()

    return AssetFactoryResponse(
        assets=[],
        jobs=[trino_heartbeat_monitor_job],
        schedules=[
            dg.ScheduleDefinition(
                name="trino_heartbeat_monitor_schedule",
                job=trino_heartbeat_monitor_job,
                cron_schedule="*/15 * * * *",
            )
        ],
    )
