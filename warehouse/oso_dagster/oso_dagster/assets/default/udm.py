import functools

import dagster as dg
from oso_dagster.factories.common import (
    AssetFactoryResponse,
    early_resources_asset_factory,
)
from oso_dagster.resources.udm_engine_adapter import (
    UserDefinedModelEngineAdapterResource,
)
from oso_dagster.resources.udm_state import UserDefinedModelStateResource
from scheduler.evaluator import UserDefinedModelEvaluator


@early_resources_asset_factory()
def udm_models() -> AssetFactoryResponse:
    @dg.asset
    async def udm_models(
        context: dg.AssetExecutionContext,
        udm_engine_adapter: dg.ResourceParam[UserDefinedModelEngineAdapterResource],
        udm_state: dg.ResourceParam[UserDefinedModelStateResource],
    ) -> None:
        async with udm_state.get_client() as udm_client:
            evaluator = UserDefinedModelEvaluator.prepare(udm_client)
            await evaluator.evaluate(
                functools.partial(
                    udm_engine_adapter.get_adapter, log_override=context.log
                )
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
