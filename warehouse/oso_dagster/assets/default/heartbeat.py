"""
Mostly testing job for debugging heartbeat resource implementations.
"""

import dagster as dg
from oso_dagster.factories.common import AssetFactoryResponse
from oso_dagster.resources.heartbeat import HeartBeatResource


class HeartbeatConfig(dg.Config):
    job_name: str


def heartbeat_factory() -> AssetFactoryResponse:
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

    return AssetFactoryResponse(
        assets=[],
        jobs=[heartbeat_fake_beat_job, heartbeat_get_last_heartbeat_job],
    )
