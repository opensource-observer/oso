import dagster as dg
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import (
    AssetFactoryResponse,
    early_resources_asset_factory,
)
from oso_dagster.resources.trino import TrinoResource
from scheduler.evaluator import evaluate_all_models
from sqlmesh.core.engine_adapter.trino import TrinoEngineAdapter


@early_resources_asset_factory()
def udm_models() -> AssetFactoryResponse:
    @dg.asset
    async def udm_models(
        context: dg.AssetExecutionContext,
        trino: dg.ResourceParam[TrinoResource],
        global_config: dg.ResourceParam[DagsterConfig],
    ) -> None:
        # TODO replace with a real UDM client
        # For now we have a fake implementation we use from the testing module
        from scheduler.testing.client import FakeUDMClient

        async with trino.ensure_available():
            adapter = TrinoEngineAdapter(
                connection_factory_or_pool=lambda: trino.get_connection()
            )

            await evaluate_all_models(
                udm_client=FakeUDMClient(),
                adapter=adapter,
            )

    job = dg.define_asset_job(
        name="udm_models_job", selection=dg.AssetSelection.assets(udm_models)
    )

    return AssetFactoryResponse(
        assets=[udm_models],
        jobs=[job],
        # Run this job every 2 hours to evaluate UDM models
        schedules=[dg.ScheduleDefinition(job=job, cron_schedule="0 */2 * * *")],
    )
