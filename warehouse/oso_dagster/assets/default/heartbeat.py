"""
Mostly testing job for debugging heartbeat resource implementations.
"""

import dagster as dg
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import (
    AssetFactoryResponse,
    early_resources_asset_factory,
)
from oso_dagster.resources.heartbeat import HeartBeatResource


class HeartbeatConfig(dg.Config):
    job_name: str


@early_resources_asset_factory()
def heartbeat_factory(global_config: DagsterConfig) -> AssetFactoryResponse:
    @dg.op
    async def heartbeat_fake_beat(
        config: HeartbeatConfig, heartbeat: HeartBeatResource
    ) -> None:
        await heartbeat.beat(config.job_name)

    @dg.job(executor_def=dg.in_process_executor)
    def heartbeat_fake_beat_job():
        heartbeat_fake_beat()

    @dg.op
    async def heartbeat_get_last_heartbeat(
        config: HeartbeatConfig, heartbeat: HeartBeatResource
    ) -> None:
        last_beat = await heartbeat.get_last_heartbeat_for(config.job_name)
        if last_beat:
            dg.get_dagster_logger().info(
                f"Last heartbeat for job {config.job_name}: {last_beat.isoformat()}"
            )
        else:
            dg.get_dagster_logger().info(
                f"No heartbeat found for job {config.job_name}"
            )

    @dg.job(executor_def=dg.in_process_executor)
    def heartbeat_get_last_heartbeat_job():
        heartbeat_get_last_heartbeat()

    @dg.asset
    async def heartbeat_test_asset(
        context: dg.AssetExecutionContext, heartbeat: HeartBeatResource
    ) -> dg.MaterializeResult:
        # Return a basic dataframe with a row of data with 3 columns

        async with heartbeat.heartbeat(
            "heartbeat_noop_asset", interval_seconds=5, log_override=context.log
        ):
            # Intentionally do some work here to simulate a long running asset
            # that consumes a lot of cpu
            def fibonacci(n):
                if n <= 1:
                    return n
                else:
                    return fibonacci(n - 1) + fibonacci(n - 2)

            for i in range(40):
                context.log.info(f"Fibonacci({i}) = {fibonacci(i)}")
            context.log.info("Heartbeat asset completed work")
            return dg.MaterializeResult(metadata={"info": "Heartbeat asset completed"})

    assets = []
    if global_config.test_assets_enabled:
        assets.append(heartbeat_test_asset)

    return AssetFactoryResponse(
        assets=assets,
        jobs=[heartbeat_fake_beat_job, heartbeat_get_last_heartbeat_job],
    )
