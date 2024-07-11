from dagster import (
    run_failure_sensor,
    RunFailureSensorContext,
    DefaultSensorStatus,
    op,
    job,
    RunRequest,
    RunConfig,
    Config,
    OpExecutionContext,
    DagsterEventType,
)
from ..utils import AlertManager
from .common import AssetFactoryResponse


class AlertOpConfig(Config):
    run_id: str


def setup_alert_sensor(name: str, base_url: str, alert_manager: AlertManager):
    @op(name=f"{name}_alert_op")
    def failure_op(context: OpExecutionContext, config: AlertOpConfig) -> None:
        context.log.info(config.run_id)
        instance = context.instance
        stats = instance.get_run_stats(config.run_id)
        context.log.info(stats)
        records = instance.get_records_for_run(config.run_id).records
        context.log.info(records)
        events = [
            record.event_log_entry for record in records if record.event_log_entry
        ]
        dagster_events = [
            event.dagster_event for event in events if event.dagster_event
        ]
        failures = [event for event in dagster_events if event.is_failure]
        step_failures = [
            failure
            for failure in failures
            if failure.event_type in [DagsterEventType.STEP_FAILURE]
        ]

        alert_manager.alert(
            f"{len(step_failures)} failed steps in run ({base_url}/runs/{config.run_id})"
        )

    @job(name=f"{name}_alert_job")
    def failure_job():
        failure_op()

    @run_failure_sensor(
        name=name, default_status=DefaultSensorStatus.RUNNING, request_job=failure_job
    )
    def failure_sensor(context: RunFailureSensorContext):
        yield RunRequest(
            run_key=context.dagster_run.run_id,
            run_config=RunConfig(
                ops={
                    f"{name}_alert_op": {
                        "config": {
                            "run_id": context.dagster_run.run_id,
                        }
                    }
                }
            ),
        )

    return AssetFactoryResponse([], sensors=[failure_sensor], jobs=[failure_job])
